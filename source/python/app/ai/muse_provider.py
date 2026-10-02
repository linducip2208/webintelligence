"""Muse Spark 1.3 via OpenAI-compatible chat completions. No hardcode: all from config."""
import json, urllib.request
class MuseSparkProvider:
    name = "muse-spark"
    def __init__(self, base_url, api_key, model="muse-spark-1.3", timeout=60):
        self.base_url = base_url.rstrip("/"); self.api_key = api_key
        self.model = model; self.timeout = timeout
    def chat(self, messages, model=""):
        if not self.base_url or not self.api_key: return {"error": "not-configured"}
        body = json.dumps({"model": model or self.model, "messages": messages}).encode()
        req = urllib.request.Request(self.base_url + "/chat/completions", data=body,
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + self.api_key})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                return json.loads(r.read().decode())
        except Exception as e: return {"error": str(e)}
    def structured_output(self, messages, schema, model=""):
        r = self.chat(messages + [{"role": "system", "content": "Return JSON matching: " + json.dumps(schema)}], model)
        return r
    def health_check(self):
        if not self.base_url or not self.api_key: return {"ok": False, "reason": "not-configured"}
        return {"ok": True, "model": self.model}
    def estimate_cost(self, inp, out): return round(inp*1.5e-6 + out*6e-6, 6)
