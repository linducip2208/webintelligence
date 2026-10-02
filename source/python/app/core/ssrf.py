"""SSRF guard — stdlib only. Blocks private/loopback/link-local/metadata."""
import ipaddress, urllib.parse
BLOCKED_NETS = [
    ipaddress.ip_network("127.0.0.0/8"), ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("10.0.0.0/8"), ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"), ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("fc00::/7"), ipaddress.ip_network("fe80::/10"),
]
METADATA_IPS = {"169.254.169.254", "fd00:ec2::254"}
ALLOWED_SCHEMES = {"http", "https"}
class SSRFError(ValueError): pass
def _allowed_by_trust(ip: ipaddress._BaseAddress, trusted):
    for c in trusted or []:
        try:
            if ip in ipaddress.ip_network(c, strict=False): return True
        except ValueError: continue
    return False
def validate_url(url: str, trusted_cidrs=None):
    if not url or len(url) > 2048: raise SSRFError("bad url length")
    p = urllib.parse.urlparse(url)
    if p.scheme not in ALLOWED_SCHEMES: raise SSRFError(f"scheme not allowed: {p.scheme}")
    if not p.hostname: raise SSRFError("missing host")
    host = p.hostname.lower()
    # literal-IP check
    try:
        ip = ipaddress.ip_address(host.strip("[]"))
    except ValueError:
        if host in ("localhost", "metadata.google.internal"):
            raise SSRFError("host blocked")
        return True
    if str(ip) in METADATA_IPS:
        raise SSRFError("cloud metadata blocked")
    if any(ip in n for n in BLOCKED_NETS) and not _allowed_by_trust(ip, trusted_cidrs):
        raise SSRFError(f"private/loopback IP blocked: {ip}")
    return True
