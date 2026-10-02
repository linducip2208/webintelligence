"""OpenAI-compatible provider base (OpenAI, Muse Spark, Ollama, any compat endpoint)."""
from .http import post_json, get_json, estimate_tokens, messages_text, AIError


class OpenAICompatProvider:
    def __init__(self, base_url, api_key="", model="", name="compat",
                 timeout=60, price_in=0.0, price_out=0.0):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model
        self.name = name
        self.timeout = timeout
        self.price_in = price_in
        self.price_out = price_out

    @property
    def configured(self):
        return bool(self.base_url)

    def _headers(self):
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = "Bearer " + self.api_key
        return h

    def chat(self, messages, model=""):
        if not self.configured:
            return {"error": "not-configured"}
        mdl = model or self.model
        try:
            r = post_json(self.base_url + "/chat/completions", self._headers(),
                          {"model": mdl, "messages": messages}, self.timeout)
            d = r["data"]
            txt = d["choices"][0]["message"]["content"]
            usage = d.get("usage", {})
            return {"text": txt, "model": mdl,
                    "input_tokens": usage.get("prompt_tokens", estimate_tokens(messages_text(messages))),
                    "output_tokens": usage.get("completion_tokens", estimate_tokens(txt or "")),
                    "latency_ms": r["latency_ms"]}
        except (AIError, KeyError, IndexError, TypeError) as e:
            return {"error": str(e)[:300]}

    def structured_output(self, messages, schema, model=""):
        msgs = list(messages or []) + [
            {"role": "system", "content": "Return ONLY valid JSON matching this schema: " + str(schema)}]
        out = self.chat(msgs, model)
        if "error" in out:
            return out
        import json as _j
        try:
            out["data"] = _j.loads(out.get("text", ""))
        except Exception as e:
            out["error"] = f"bad-json: {e}"
        return out

    def stream(self, messages, model=""):
        """True SSE streaming via http.client; yields {"delta": text} pieces."""
        import http.client as _hc
        import urllib.parse as _up
        if not self.configured:
            yield {"error": "not-configured"}
            return
        import json as _j
        u = _up.urlparse(self.base_url + "/chat/completions")
        body = _j.dumps({"model": model or self.model, "messages": messages,
                         "stream": True}).encode()
        conn = _hc.HTTPConnection(u.hostname, u.port or 80, timeout=self.timeout)
        try:
            conn.request("POST", u.path or "/", body, self._headers())
            resp = conn.getresponse()
            buf = b""
            while True:
                chunk = resp.read(1024)
                if not chunk:
                    break
                buf += chunk
                while b"\n" in buf:
                    line, buf = buf.split(b"\n", 1)
                    line = line.strip()
                    if line.startswith(b"data:"):
                        payload = line[5:].strip()
                        if payload == b"[DONE]":
                            return
                        try:
                            d = _j.loads(payload)
                            piece = d["choices"][0]["delta"].get("content", "")
                            if piece:
                                yield {"delta": piece}
                        except Exception:
                            continue
        except Exception as e:
            yield {"error": str(e)[:200]}
        finally:
            try:
                conn.close()
            except Exception:
                pass

    def list_models(self):
        if not self.configured:
            return {"error": "not-configured"}
        try:
            r = get_json(self.base_url + "/models", self._headers(), 30)
            ids = [m.get("id") for m in r["data"].get("data", []) if m.get("id")]
            return {"models": ids}
        except AIError as e:
            return {"error": str(e)[:300]}

    def health_check(self):
        if not self.configured:
            return {"ok": False, "reason": "not-configured"}
        r = self.list_models()
        if "error" in r:
            # some compat endpoints lack /models; verify base responds instead
            try:
                post_json(self.base_url + "/chat/completions", self._headers(),
                          {"model": self.model, "messages": [], "max_tokens": 1}, 10)
                return {"ok": True, "model": self.model, "note": "no-models-endpoint"}
            except AIError as e:
                return {"ok": False, "reason": str(e)[:200]}
        return {"ok": True, "models": r["models"]}

    def estimate_cost(self, inp, out):
        return round(inp * self.price_in + out * self.price_out, 6)
