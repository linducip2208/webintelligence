"""Build configured providers from environment. Only providers with the
required settings are instantiated — nothing hardcoded as mandatory."""
import os


def build_all(get=os.getenv):
    from .vendors import (MuseSparkProvider, OpenAIProvider, AnthropicProvider,
                          GoogleProvider, OllamaProvider)
    out = {}
    if get("MUSE_SPARK_BASE_URL"):
        out["muse-spark"] = MuseSparkProvider(
            get("MUSE_SPARK_BASE_URL"), get("MUSE_SPARK_API_KEY", ""),
            get("MUSE_SPARK_MODEL", "muse-spark-1.3"))
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
