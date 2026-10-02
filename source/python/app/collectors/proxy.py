class ProxyProvider:
    def get_proxy(self, region=""): raise NotImplementedError
    def release_proxy(self, proxy, ok=True): pass
    def health_check(self): return {"ok": True}
class OwnProxyProvider(ProxyProvider):
    def __init__(self, urls): self.urls = list(urls or []); self.i = 0; self.used = {u: 0 for u in self.urls}
    def get_proxy(self, region=""):
        if not self.urls: return None
        u = self.urls[self.i % len(self.urls)]; self.i += 1; self.used[u] += 1; return u
    def release_proxy(self, proxy, ok=True): pass
    def health_check(self): return {"ok": bool(self.urls), "pool": len(self.urls), "used": self.used}
