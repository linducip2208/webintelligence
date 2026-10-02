"""Bright Data adapter — config from env/DB, never hardcoded."""
import json, urllib.request
class BrightDataProvider:
    kind = "brightdata"
    def __init__(self, api_key="", zone="", endpoint="https://api.brightdata.com"):
        self.api_key = api_key; self.zone = zone; self.endpoint = endpoint.rstrip("/")
        self.errors = []
    @property
    def configured(self): return bool(self.api_key and self.zone)
    def get_proxy(self, region=""):
        if not self.configured: return None
        return f"http://{self.zone}:{self.api_key}@proxy.brightdata.com:22225"
    def release_proxy(self, proxy, ok=True): pass
    def health_check(self):
        if not self.configured: return {"ok": False, "reason": "not-configured"}
        return {"ok": True, "zone": self.zone}
    def test_connection(self, timeout=15):
        if not self.configured: return {"ok": False, "reason": "missing BRIGHTDATA_API_KEY/ZONE"}
        try:
            req = urllib.request.Request(self.endpoint + "/status", headers={"Authorization": f"Bearer {self.api_key}"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return {"ok": r.status == 200, "status": r.status}
        except Exception as e:
            self.errors.append(str(e)); return {"ok": False, "error": str(e)}
