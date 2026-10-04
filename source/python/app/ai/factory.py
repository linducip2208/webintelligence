"""Build configured providers from environment. Only providers with the
required settings are instantiated — nothing hardcoded as mandatory."""
import os


def build_provider(protocol, base_url, api_key="", model=""):
    """Instantiate the right provider class for a protocol name.

    Lets callers (env factory, DB-provider path, custom slots) add new
    endpoints without touching provider code: protocol is data.
    Supported: chat (any OpenAI-compatible), responses, anthropic, google.
    """
    proto = (protocol or "chat").lower()
    if proto == "responses":
        from .responses_provider import ResponsesProvider
        return ResponsesProvider(base_url, api_key, model or "default-model")
    if proto == "anthropic":
        from .vendors import AnthropicProvider
        return AnthropicProvider(api_key, model or "claude-3-5-haiku-latest")
    if proto == "google":
        from .vendors import GoogleProvider
        return GoogleProvider(api_key, model or "gemini-2.0-flash",
                              base_url=base_url or "https://generativelanguage.googleapis.com")
    from .muse_provider import MuseSparkProvider
    return MuseSparkProvider(base_url, api_key, model or "muse-spark-1.3")


def build_all(get=os.getenv):
    from .vendors import (OpenAIProvider, AnthropicProvider,
                          GoogleProvider, OllamaProvider)
    out = {}
    if get("MUSE_SPARK_BASE_URL"):
        out["muse-spark"] = build_provider(
            get("MUSE_SPARK_PROTOCOL", "chat"),
            get("MUSE_SPARK_BASE_URL"), get("MUSE_SPARK_API_KEY", ""),
            get("MUSE_SPARK_MODEL", "muse-spark-1.3"))
    if get("CUSTOM_AI_BASE_URL"):
        from .openai_compat import OpenAICompatProvider
        from .responses_provider import ResponsesProvider
        name = get("CUSTOM_AI_NAME", "custom") or "custom"
        if (get("CUSTOM_AI_PROTOCOL", "chat") or "chat").lower() == "responses":
            out[name] = ResponsesProvider(
                get("CUSTOM_AI_BASE_URL"), get("CUSTOM_AI_API_KEY", ""),
                get("CUSTOM_AI_MODEL", "custom-model"))
        else:
            out[name] = OpenAICompatProvider(
                get("CUSTOM_AI_BASE_URL"), get("CUSTOM_AI_API_KEY", ""),
                get("CUSTOM_AI_MODEL", "custom-model"), name)
    if get("OPENAI_API_KEY"):
        out["openai"] = OpenAIProvider(get("OPENAI_API_KEY"),
                                       get("OPENAI_MODEL", "gpt-4o-mini"))
    if get("ANTHROPIC_API_KEY"):
        out["anthropic"] = AnthropicProvider(get("ANTHROPIC_API_KEY"),
                                             get("ANTHROPIC_MODEL", "claude-3-5-haiku-latest"))
    if get("GOOGLE_API_KEY"):
        out["google"] = GoogleProvider(get("GOOGLE_API_KEY"),
                                       get("GOOGLE_MODEL", "gemini-2.0-flash"))
    if get("OLLAMA_BASE_URL", "") != "disabled":
        out["ollama"] = OllamaProvider(get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
                                       get("OLLAMA_MODEL", "llama3.1"))
    return out


def fallback_order(get=os.getenv):
    raw = get("AI_FALLBACKS", "")
    return [x.strip() for x in raw.split(",") if x.strip()]
