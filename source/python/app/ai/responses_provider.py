"""OpenAI Responses-protocol provider (e.g. Muse Spark via OpenCode Go gateway).

Same AIProvider interface as OpenAICompatProvider, but speaks:
  POST {base_url}/responses   {"model": ..., "input": [...]}
instead of /chat/completions. Response text is read from `output_text`
or walked out of `output[]` message items. SSE streaming consumes
`response.output_text.delta` events.
"""
from .http import post_json, get_json, estimate_tokens, messages_text, AIError

# Stable per-process session id: the OpenCode gateway requires clients to
# identify with a non-generic User-Agent plus a stable x-opencode-session
# per conversation for routing/prompt caching. Plain Python-urllib requests
# are rejected at the edge (Cloudflare 1010).
import uuid as _uuid
_SESSION_ID = str(_uuid.uuid4())
_USER_AGENT = "webintel/2.11"


class ResponsesProvider:
    name = "muse-spark"

    def __init__(self, base_url="", api_key="", model="muse-spark-1.3",
                 timeout=60, price_in=0.0, price_out=0.0):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model
        self.timeout = timeout
        self.price_in = price_in
        self.price_out = price_out

    @property
    def configured(self):
        return bool(self.base_url)

    def _headers(self):
        h = {"Content-Type": "application/json", "User-Agent": _USER_AGENT,
             "x-opencode-session": _SESSION_ID}
        if self.api_key:
            h["Authorization"] = "Bearer " + self.api_key
        return h

    @staticmethod
    def _to_input(messages):
        items = []
        for m in messages or []:
            role = m.get("role", "user")
            if role not in ("user", "assistant", "system", "developer"):
                role = "user"
            c = m.get("content", "")
            if not isinstance(c, str):
                import json as _j
                c = _j.dumps(c, default=str)
            items.append({"role": role, "content": c})
        return items

    @staticmethod
    def _extract_text(data):
        if isinstance(data.get("output_text"), str) and data["output_text"]:
            return data["output_text"]
        parts = []
        for item in data.get("output") or []:
            if not isinstance(item, dict) or item.get("type") != "message":
                continue
            for c in item.get("content") or []:
                if isinstance(c, dict) and c.get("type") == "output_text" and c.get("text"):
                    parts.append(c["text"])
        return "".join(parts)

    @staticmethod
    def _usage(data, messages, text):
        u = data.get("usage") or {}
        return (u.get("input_tokens", estimate_tokens(messages_text(messages))),
                u.get("output_tokens", estimate_tokens(text or "")))

    def chat(self, messages, model=""):
        if not self.configured:
            return {"error": "not-configured"}
        mdl = model or self.model
        try:
            r = post_json(self.base_url + "/responses", self._headers(),
                          {"model": mdl, "input": self._to_input(messages),
                           "stream": False}, self.timeout)
            d = r["data"]
            txt = self._extract_text(d)
            if not txt:
                return {"error": f"empty-response: {str(d)[:200]}"}
            inp, out = self._usage(d, messages, txt)
            return {"text": txt, "model": mdl, "input_tokens": inp,
                    "output_tokens": out, "latency_ms": r["latency_ms"]}
        except (AIError, KeyError, IndexError, TypeError) as e:
            return {"error": str(e)[:300]}

    def structured_output(self, messages, schema, model=""):
        msgs = list(messages or []) + [
            {"role": "user", "content": "Return ONLY valid JSON matching: " + str(schema)}]
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
        import http.client as _hc
        import urllib.parse as _up
        if not self.configured:
            yield {"error": "not-configured"}
            return
        import json as _j
        u = _up.urlparse(self.base_url + "/responses")
        body = _j.dumps({"model": model or self.model,
                         "input": self._to_input(messages),
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
                    if not line.startswith(b"data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == b"[DONE]":
                        return
                    try:
                        d = _j.loads(payload)
                    except Exception:
                        continue
                    if d.get("type") == "response.output_text.delta" and d.get("delta"):
                        yield {"delta": d["delta"]}
                    elif d.get("type") == "response.completed":
                        return
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

    def discover_models(self):
        """Gateway-aware discovery with per-model protocol/endpoint metadata."""
        if not self.configured:
            return {"models": [], "error": {"code": "INVALID_CONFIGURATION",
                                            "message": "Provider endpoint missing."}}
        from . import go_discovery as _go
        return _go.discover(self.base_url, self._headers(), self.timeout)

    def health_check(self):
        if not self.configured:
            return {"ok": False, "reason": "not-configured"}
        r = self.list_models()
        if "error" not in r:
            return {"ok": True, **r}
        # gateway without /models: cheap probe call instead (min 16 tokens)
        try:
            post_json(self.base_url + "/responses", self._headers(),
                      {"model": self.model, "input": "ping",
                       "max_output_tokens": 16}, 15)
            return {"ok": True, "model": self.model, "note": "probe-ok-no-models-endpoint"}
        except AIError as e:
            return {"ok": False, "reason": str(e)[:300]}

    def estimate_cost(self, inp, out):
        return round(inp * self.price_in / 1000 + out * self.price_out / 1000, 6)
