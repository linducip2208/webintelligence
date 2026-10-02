"""SSRF guard — stdlib only. Hostile-network safe.

Blocks: loopback/private/link-local/multicast/reserved (via is_global),
cloud metadata, decimal/hex/octal IP tricks, userinfo tricks (urlsplit),
alternate schemes. Resolves DNS and validates EVERY returned address
(DNS-rebinding safe). Redirect targets must be revalidated by callers.
"""
import ipaddress
import re
import socket
import urllib.parse

METADATA_IPS = {"169.254.169.254", "fd00:ec2::254", "100.100.100.200"}
BLOCKED_NAMES = {"localhost", "metadata.google.internal",
                 "metadata.google.internal."}
ALLOWED_SCHEMES = {"http", "https"}


class SSRFError(ValueError):
    pass


def _allowed_by_trust(ip, trusted):
    for c in trusted or []:
        try:
            if ip in ipaddress.ip_network(c, strict=False):
                return True
        except ValueError:
            continue
    return False


def _normalize_numeric(host: str):
    """Turn decimal/hex/octal IPv4 tricks into dotted form, else None."""
    h = host.strip("[]")
    full = None
    if re.fullmatch(r"\d+", h):
        full = int(h)  # decimal like 2130706433
    elif re.fullmatch(r"0[xX][0-9a-fA-F]+", h):
        full = int(h, 16)
    elif re.fullmatch(r"0[0-7]+", h):
        try:
            full = int(h, 8)
        except ValueError:
            full = None
    if full is not None and 0 <= full <= 0xFFFFFFFF:
        return str(ipaddress.ip_address(full))
    if "." in h:
        parts = []
        for part in h.split("."):
            try:
                if part.lower().startswith("0x"):
                    parts.append(str(int(part, 16)))
                    continue
                if re.fullmatch(r"0[0-7]+", part):
                    parts.append(str(int(part, 8)))
                    continue
                parts.append(str(int(part)))
            except ValueError:
                return None
        if len(parts) == 4 and all(0 <= int(x) <= 255 for x in parts):
            return ".".join(parts)
    return None


def _check_ip(ip, trusted_cidrs):
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        ip = ip.ipv4_mapped
    if ip.compressed in METADATA_IPS or str(ip) in METADATA_IPS:
        raise SSRFError(f"cloud metadata blocked: {ip}")
    if not ip.is_global and not _allowed_by_trust(ip, trusted_cidrs):
        raise SSRFError(f"non-public IP blocked: {ip}")
    return ip


def validate_url(url: str, trusted_cidrs=None):
    if not url or len(url) > 2048:
        raise SSRFError("bad url length")
    p = urllib.parse.urlparse(url)
    if p.scheme not in ALLOWED_SCHEMES:
        raise SSRFError(f"scheme not allowed: {p.scheme}")
    if not p.hostname:
        raise SSRFError("missing host")
    host = p.hostname.lower().rstrip(".")
    if host in BLOCKED_NAMES:
        raise SSRFError(f"host blocked: {host}")
    dotted = _normalize_numeric(host)
    literal = dotted or host.strip("[]")
    try:
        _check_ip(ipaddress.ip_address(literal), trusted_cidrs)
        return True
    except ValueError:
        pass
    # DNS name: resolve every address and validate each (rebinding-safe)
    try:
        infos = socket.getaddrinfo(host, None, family=socket.AF_UNSPEC,
                                   type=socket.SOCK_STREAM)
    except OSError:
        raise SSRFError(f"dns failed for {host}")
    ips = []
    for fam, _, _, _, sockaddr in infos:
        try:
            ips.append(ipaddress.ip_address(sockaddr[0]))
        except ValueError:
            continue
    if not ips:
        raise SSRFError(f"dns gave no addresses for {host}")
    for ip in ips:
        _check_ip(ip, trusted_cidrs)
    return True
