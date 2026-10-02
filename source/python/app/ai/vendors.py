"""Vendor providers: OpenAI, Anthropic, Google Gemini, Ollama, Muse Spark.

All implement the AIProvider interface; all config-driven; none hardcoded
as the single vendor. Selection happens via registry + fallback chain.
"""
from .http import post_json, get_json, estimate_tokens, messages_text, AIError
from .openai_compat import OpenAICompatProvider

# per-1K-token USD estimates (config-overridable, documented as estimates)
OPENAI_PRICES = {"gpt-4o-mini": (0.00015, 0.0006), "gpt-4o": (0.0025, 0.01)}
ANTHROPIC_PRICES = {"claude-3-5-haiku-latest": (0.0008, 0.004),
                    "claude-sonnet-4-20250514": (0.003, 0.015)}
GOOGLE_PRICES = {"gemini-2.0-flash": (0.0001, 0.0004)}


class OpenAIProvider(OpenAICompatProvider):
    def __init__(self, api_key="", model="gpt-4o-mini", timeout=60, prices=None):
        p = prices or dict(OPENAI_PRICES)
        pi, po = p.get(model, (0.0, 0.0))
        super().__init__("https://api.openai.com/v1", api_key, model,
                         "openai", timeout, pi, po)

    @property
    def configured(self):
        return bool(self.api_key)


class MuseSparkProvider(OpenAICompatProvider):
    """Muse Spark 1.3 served over an OpenAI-compatible endpoint (config-driven)."""

    def __init__(self, base_url="", api_key="", model="muse-spark-1.3",
                 timeout=60, price_in=1.5e-6 * 1000, price_out=6e-6 * 1000):
        super().__init__(base_url, api_key, model, "muse-spark", timeout,
                         price_in / 1000, price_out / 1000)


class OllamaProvider(OpenAICompatProvider):
    """Local Ollama (default http://127.0.0.1:11434/v1). Zero vendor cost."""

    def __init__(self, base_url="http://127.0.0.1:11434/v1", model="llama3.1",
                 timeout=120):
        super().__init__(base_url, "", model, "ollama", timeout, 0.0, 0.0)


class AnthropicProvider:
    name = "anthropic"

    def __init__(self, api_key="", model="claude-3-5-haiku-latest",
                 timeout=60, prices=None, base_url="https://api.anthropic.com"):
        p = prices or dict(ANTHROPIC_PRICES)
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.base_url = base_url.rstrip("/")
        self.price_in, self.price_out = p.get(model, (0.0, 0.0))

    @property
    def configured(self):
        return bool(self.api_key)

    def _headers(self):
        return {"Content-Type": "application/json", "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"}

    def _split(self, messages):
        system, rest = [], []
        for m in messages or []:
            (system if m.get("role") == "system" else rest).append(m)
        sys_txt = "\n".join(x.get("content", "") for x in system if isinstance(x.get("content"), str))
        conv = [{"role": ("assistant" if m.get("role") == "assistant" else "user"),
                 "content": m.get("content", "")} for m in rest]
        return sys_txt, conv

    def chat(self, messages, model=""):
        if not self.configured:
            return {"error": "not-configured"}
        mdl = model or self.model
        sys_txt, conv = self._split(messages)
        payload = {"model": mdl, "max_tokens": 1024, "messages": conv}
        if sys_txt:
            payload["system"] = sys_txt
        try:
            r = post_json(self.base_url + "/messages",
                          self._headers(), payload, self.timeout)
            d = r["data"]
            txt = "".join(b.get("text", "") for b in d.get("content", [])
                          if b.get("type") == "text")
            u = d.get("usage", {})
            return {"text": txt, "model": mdl,
                    "input_tokens": u.get("input_tokens", estimate_tokens(messages_text(messages))),
                    "output_tokens": u.get("output_tokens", estimate_tokens(txt)),
                    "latency_ms": r["latency_ms"]}
        except (AIError, KeyError, TypeError) as e:
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
        yield {"error": "streaming not implemented for anthropic; use chat"}

    def list_models(self):
        if not self.configured:
            return {"error": "not-configured"}
        try:
            r = get_json(self.base_url + "/models", self._headers(), 30)
            return {"models": [m.get("id") for m in r["data"].get("data", [])]}
        except AIError as e:
            return {"error": str(e)[:300]}

    def health_check(self):
        if not self.configured:
            return {"ok": False, "reason": "not-configured"}
        r = self.list_models()
        return {"ok": "error" not in r, **r}

    def estimate_cost(self, inp, out):
        return round(inp * self.price_in / 1000 + out * self.price_out / 1000, 6)


class GoogleProvider:
    name = "google"

    def __init__(self, api_key="", model="gemini-2.0-flash", timeout=60, prices=None,
                 base_url="https://generativelanguage.googleapis.com"):
        p = prices or dict(GOOGLE_PRICES)
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.base_url = base_url.rstrip("/")
        self.price_in, self.price_out = p.get(model, (0.0, 0.0))

    @property
    def configured(self):
        return bool(self.api_key)

    def chat(self, messages, model=""):
        if not self.configured:
            return {"error": "not-configured"}
        mdl = model or self.model
        parts = [{"text": messages_text(messages)}]
        url = (f"{self.base_url}/v1beta/models/{mdl}"
               f":generateContent?key={self.api_key}")
        try:
            r = post_json(url, {"Content-Type": "application/json"},
                          {"contents": [{"parts": parts}]}, self.timeout)
            d = r["data"]
            txt = "".join(p.get("text", "") for p in
                          d["candidates"][0]["content"].get("parts", []))
            u = d.get("usageMetadata", {})
            return {"text": txt, "model": mdl,
                    "input_tokens": u.get("promptTokenCount", estimate_tokens(messages_text(messages))),
                    "output_tokens": u.get("candidatesTokenCount", estimate_tokens(txt)),
                    "latency_ms": r["latency_ms"]}
        except (AIError, KeyError, IndexError, TypeError) as e:
            return {"error": str(e)[:300]}

    def structured_output(self, messages, schema, model=""):
        mdl = model or self.model
        parts = [{"text": messages_text(messages) +
                  "\nReturn ONLY valid JSON matching: " + str(schema)}]
        url = (f"{self.base_url}/v1beta/models/{mdl}"
               f":generateContent?key={self.api_key}")
        try:
            r = post_json(url, {"Content-Type": "application/json"},
                          {"contents": [{"parts": parts}],
                           "generationConfig": {"responseMimeType": "application/json"}},
                          self.timeout)
            d = r["data"]
            txt = "".join(p.get("text", "") for p in
                          d["candidates"][0]["content"].get("parts", []))
            import json as _j
            return {"text": txt, "data": _j.loads(txt), "model": mdl,
                    "latency_ms": r["latency_ms"]}
        except Exception as e:
            return {"error": str(e)[:300]}

    def stream(self, messages, model=""):
        yield {"error": "streaming not implemented for google; use chat"}

    def list_models(self):
        return {"error": "list via https://ai.google.dev/models"}

    def health_check(self):
        if not self.configured:
            return {"ok": False, "reason": "not-configured"}
        return {"ok": True, "model": self.model, "note": "key present; live call needs quota"}

    def estimate_cost(self, inp, out):
        return round(inp * self.price_in / 1000 + out * self.price_out / 1000, 6)
