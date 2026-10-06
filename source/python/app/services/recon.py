"""Passive recon enrichment — stdlib only, bounded, SSRF-guarded.

For one already-fetched target URL, adds: DNS IPs, TLS certificate summary,
page title/tech/links stats, robots.txt presence. Never raises; every leg
reports ok/error independently. No port scanning, no intrusive probing —
single-host, read-only, analyst-authorized target only.
"""
import hashlib
import re
import socket
import ssl
import time
import urllib.parse as _up

try:  # package context
    from ..core.ssrf import validate_url
except ImportError:  # flat test context
    from core.ssrf import validate_url

TECH_SIGNS = [
    ("WordPress", re.compile(r"wp-content|wp-includes|wp-json", re.I)),
    ("Joomla", re.compile(r"joomla|/media/jui/", re.I)),
    ("Drupal", re.compile(r"drupal|sites/default/files", re.I)),
    ("jQuery", re.compile(r"jquery(\.min)?\.js", re.I)),
    ("React", re.compile(r"react(-dom)?(\.min)?\.js|___react|data-reactroot", re.I)),
    ("Next.js", re.compile(r"__NEXT_DATA__|_next/static", re.I)),
    ("Vue", re.compile(r"vue(\.min)?\.js|data-v-", re.I)),
    ("Angular", re.compile(r"ng-version|angular(\.min)?\.js", re.I)),
    ("Bootstrap", re.compile(r"bootstrap(\.min)?\.(css|js)", re.I)),
    ("Cloudflare", re.compile(r"cloudflare|cf-chl|__cf_bm", re.I)),
    ("Google Analytics", re.compile(r"googletagmanager|google-analytics", re.I)),
    ("PHP", re.compile(r"\.php([?\"'])", re.I)),
]


def _host_of(url):
    try:
        return (_up.urlsplit(url).hostname or "").lower()
    except Exception:
        return ""


def dns_records(host, timeout=5):
    out = {"ok": False, "ips": [], "error": ""}
    if not host:
        out["error"] = "no host"
        return out
    try:
        infos = socket.getaddrinfo(host, None, family=socket.AF_UNSPEC,
                                   type=socket.SOCK_STREAM)
        seen = []
        for fam, _, _, _, sa in infos:
            ip = sa[0]
            if ip not in seen:
                seen.append(ip)
            if len(seen) >= 10:
                break
        out.update(ok=True, ips=seen)
    except Exception as e:
        out["error"] = str(e)[:160]
    return out


def tls_info(host, port=443, timeout=8):
    out = {"ok": False, "error": ""}
    if not host:
        out["error"] = "no host"
        return out
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            with ctx.wrap_socket(sock, server_hostname=host) as ss:
                cert = ss.getpeercert() or {}
        san = [v for (k, v) in (cert.get("subjectAltName") or []) if k == "DNS"]
        subj = {k: v for ((k, v),) in
                [t for t in (cert.get("subject") or []) if t]} if cert.get("subject") else {}
        iss = {k: v for ((k, v),) in
               [t for t in (cert.get("issuer") or []) if t]} if cert.get("issuer") else {}
        key = hashlib.sha256(
            ("|".join(sorted(san)) + "|" + str(sorted(iss.items()))).encode()
        ).hexdigest()[:32]
        out.update(ok=True, subject=subj, issuer=iss, san=sorted(san),
                   not_before=str(cert.get("notBefore", "")),
                   not_after=str(cert.get("notAfter", "")),
                   serial=str(cert.get("serialNumber", "")), cert_key=key)
    except Exception as e:
        out["error"] = str(e)[:160]
    return out


def _fetch_text(url, timeout=8, cap=100_000, trusted=None):
    validate_url(url, trusted)
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 WebIntel/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read(cap + 1)[:cap]


def http_meta(url, body, timeout=8, trusted=None, headers=None):
    """Title/tech/links from the fetched body + robots.txt presence."""
    out = {"ok": False, "error": ""}
    try:
        text = (body or b"").decode("utf-8", "ignore")[:500_000]
    except Exception:
        text = ""
    host = _host_of(url)
    title = ""
    m = re.search(r"<title[^>]*>(.*?)</title>", text, re.I | re.S)
    if m:
        title = re.sub(r"\s+", " ", m.group(1)).strip()[:300]
    tech = [name for name, rx in TECH_SIGNS if rx.search(text)]
    hrefs = re.findall(r'href=["\']([^"\']+)', text, re.I)[:2000]
    domains, internal, external = set(), 0, 0
    for h in hrefs:
        if h.startswith("#") or h.startswith("javascript:"):
            continue
        if h.startswith("/") or not _up.urlsplit(h).netloc:
            internal += 1
            continue
        d = (_up.urlsplit(h).hostname or "").lower()
        if d:
            domains.add(d)
            if d == host or d.endswith("." + host):
                internal += 1
            else:
                external += 1
    robots, sitemap = False, False
    try:
        parts = _up.urlsplit(url)
        netloc = parts.netloc or host
        if netloc:
            rb = _fetch_text(f"{parts.scheme}://{netloc}/robots.txt",
                             timeout, 20_000, trusted)
            robots = True
            try:
                sitemap = "sitemap" in rb.decode("utf-8", "ignore").lower()
            except Exception:
                sitemap = False
    except Exception:
        robots = False
    out.update(ok=True, title=title, tech=tech[:12],
               links_total=len(hrefs), links_internal=internal,
               links_external=external, link_domains=sorted(domains)[:50],
               forms=len(re.findall(r"<form[\s>]", text, re.I)),
               scripts=len(re.findall(r"<script[\s>]", text, re.I)),
               robots_txt=robots, sitemap_hint=sitemap,
               security_headers={k.lower(): v for k, v in (headers or {}).items()},
               missing_security_headers=[h for h in
                   ("strict-transport-security", "content-security-policy",
                    "x-frame-options", "x-content-type-options",
                    "referrer-policy")
                   if h not in {k.lower() for k in (headers or {})}],
               content_hash=hashlib.sha256((body or b"")[:1_000_000]).hexdigest()[:32])
    return out


def recon_target(url, body=b"", timeout_s=8, trusted_cidrs=None,
                 headers=None, deep=False):
    """Full passive recon for one target URL. Never raises.
    deep=True adds reverse-DNS + RDAP + WHOIS (scan profile 'deep')."""
    t0 = time.time()
    host = _host_of(url)
    out = {"host": host, "at": t0, "ok": True, "latency_ms": 0, "deep": bool(deep)}
    try:
        validate_url(url, trusted_cidrs)
    except Exception as e:
        out.update(ok=False, error=f"url rejected: {e}")
        return out
    out["dns"] = dns_records(host, min(timeout_s, 5))
    if _up.urlsplit(url).scheme == "https":
        out["tls"] = tls_info(host, 443, min(timeout_s, 8))
    else:
        out["tls"] = {"ok": False, "error": "plain http, no TLS"}
    out["http"] = http_meta(url, body, min(timeout_s, 8), trusted_cidrs, headers)
    if deep and host and "." in host:
        out["ptr"] = reverse_dns((out["dns"] or {}).get("ips", []))
        out["rdap"] = rdap_lookup(host)
        out["whois"] = whois_lookup(host)
    out["latency_ms"] = round((time.time() - t0) * 1000, 2)
    return out


def reverse_dns(ips, timeout=4):
    """PTR records for a few IPs. Best-effort, short timeout each."""
    out = {}
    import socket as _s
    old = _s.getdefaulttimeout()
    for ip in (ips or [])[:3]:
        try:
            _s.setdefaulttimeout(timeout)
            out[ip] = _s.gethostbyaddr(ip)[0]
        except Exception:
            out[ip] = ""
    try:
        _s.setdefaulttimeout(old)
    except Exception:
        pass
    return out


def rdap_lookup(domain, timeout=10):
    """RDAP via public rdap.org proxy (optional external; honest errors)."""
    out = {"ok": False, "error": ""}
    if not domain or "." not in str(domain):
        out["error"] = "not a domain"
        return out
    try:
        import urllib.request as _u
        import json as _j
        req = _u.Request(f"https://rdap.org/domain/{domain}",
                         headers={"User-Agent": "Mozilla/5.0 WebIntel/1.0",
                                  "Accept": "application/rdap+json"})
        with _u.urlopen(req, timeout=timeout) as r:
            d = _j.loads(r.read(100_000).decode("utf-8", "ignore") or "{}")
        by_role = {}
        for e in d.get("entities", []) or []:
            roles = e.get("roles") or [""]
            by_role[roles[0]] = e
        reg = by_role.get("registrar", {}) or {}
        out.update(ok=True, registrar=str(reg.get("handle", "")),
                   status=[s for s in d.get("status", [])][:10],
                   nameservers=[n.get("ldhName", "") for n in d.get("nameservers", [])][:10],
                   raw_events=[{"action": e.get("eventAction"), "date": e.get("eventDate")}
                               for e in d.get("events", [])][:10])
    except Exception as e:
        out["error"] = str(e)[:160]
    return out


def whois_lookup(domain, timeout=8):
    """Minimal port-43 WHOIS via whois.iana.org referral (best-effort)."""
    out = {"ok": False, "error": ""}
    if not domain or "." not in str(domain):
        out["error"] = "not a domain"
        return out
    try:
        import socket as _s
        with _s.create_connection(("whois.iana.org", 43), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall((str(domain) + "\r\n").encode())
            raw = b""
            while len(raw) < 8192:
                chunk = sock.recv(2048)
                if not chunk:
                    break
                raw += chunk
        text = raw.decode("utf-8", "ignore")
        ref = ""
        for line in text.splitlines():
            if line.lower().startswith("refer:"):
                ref = line.split(":", 1)[1].strip()
                break
        out.update(ok=True, refer=ref, excerpt=text[:2000])
    except Exception as e:
        out["error"] = str(e)[:160]
    return out
