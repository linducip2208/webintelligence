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
    if get("GOOGLE_API_KEY") or get("GEMINI_API_KEY"):
        out["google"] = GoogleProvider(get("GOOGLE_API_KEY") or get("GEMINI_API_KEY", ""),
                                       get("GOOGLE_MODEL", get("GEMINI_MODEL", "gemini-2.0-flash")))
    for name, key_env, model_env, base, default_model in COMPAT_ENV:
        if get(key_env):
            out[name] = build_provider("chat", base, get(key_env, ""),
                                       get(model_env, default_model))
    if get("OPENCODE_GO_API_KEY"):
        out["opencode-go"] = build_provider(
            "responses", "https://opencode.ai/zen/go/v1",
            get("OPENCODE_GO_API_KEY", ""),
            get("OPENCODE_GO_MODEL", "muse-spark-1.3-contributor"))
    if get("OPENCODE_ZEN_API_KEY") or get("OPENCODE_API_KEY"):
        out["opencode-zen"] = build_provider(
            "chat", "https://opencode.ai/zen/go/v1",
            get("OPENCODE_ZEN_API_KEY", "") or get("OPENCODE_API_KEY", ""),
            get("OPENCODE_ZEN_MODEL", get("OPENCODE_MODEL", "")))
    if get("OLLAMA_BASE_URL", "") != "disabled":
        out["ollama"] = OllamaProvider(get("OLLAMA_BASE_URL", "http://127.0.0.1:11434/v1"),
                                       get("OLLAMA_MODEL", "llama3.1"))
    return out


#: (registry name, key env, model env, base URL, default model).
#: All speak the OpenAI chat protocol through the shared adapter.
COMPAT_ENV = (
    ("openrouter", "OPENROUTER_API_KEY", "OPENROUTER_MODEL",
     "https://openrouter.ai/api/v1", "openai/gpt-4o-mini"),
    ("groq", "GROQ_API_KEY", "GROQ_MODEL",
     "https://api.groq.com/openai/v1", "llama-3.1-8b-instant"),
    ("deepseek", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL",
     "https://api.deepseek.com/v1", "deepseek-chat"),
    ("mistral", "MISTRAL_API_KEY", "MISTRAL_MODEL",
     "https://api.mistral.ai/v1", "mistral-small-latest"),
    ("xai", "XAI_API_KEY", "XAI_MODEL",
     "https://api.x.ai/v1", "grok-3-mini"),
    ("cohere", "COHERE_API_KEY", "COHERE_MODEL",
     "https://api.cohere.ai/compatibility/v1", "command-r"),
    ("together", "TOGETHER_API_KEY", "TOGETHER_MODEL",
     "https://api.together.xyz/v1", ""),
    ("fireworks", "FIREWORKS_API_KEY", "FIREWORKS_MODEL",
     "https://api.fireworks.ai/inference/v1", ""),
    ("perplexity", "PERPLEXITY_API_KEY", "PERPLEXITY_MODEL",
     "https://api.perplexity.ai", "sonar"),
)


def fallback_order(get=os.getenv):
    raw = get("AI_FALLBACKS", "")
    return [x.strip() for x in raw.split(",") if x.strip()]
