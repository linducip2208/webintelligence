"""Centralized AI provider presets — the single source of truth for the
Add-Provider flow. Frontend renders from GET /api/v1/ai/provider-presets;
backend validates/creates from the same definitions. No duplication.

Every preset maps to a real adapter in factory.build_provider(); no
unsupported providers are listed. Capabilities describe what the ADAPTER
can do over that protocol — never claimed per-model features the platform
cannot verify. Embeddings/vision are listed only where an adapter exists.
"""
PRESETS = [
    {"id": "opencode-go", "display_name": "OpenCode Go",
     "description": "Muse and curated models through the OpenCode Go gateway (Responses API).",
     "protocol": "responses", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://opencode.ai/zen/go/v1",
     "discovery": True, "default_model": "muse-spark-1.3-contributor", "local": False,
     "capabilities": ["chat", "reasoning", "coding", "research", "summarization",
                      "classification", "structured_output", "tool_calling"]},
    {"id": "opencode-zen", "display_name": "OpenCode Zen",
     "description": "OpenCode Zen gateway over the OpenAI chat protocol. Endpoint adjustable.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "editable", "default_endpoint": "https://opencode.ai/zen/go/v1",
     "discovery": True, "default_model": "", "local": False,
     "capabilities": ["chat", "coding", "research", "summarization", "classification"]},
    {"id": "claude", "display_name": "Claude (Anthropic)",
     "description": "Anthropic Claude via the native Messages API.",
     "protocol": "anthropic", "auth": "api_key", "key_required": True,
     "key_label": "Anthropic API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.anthropic.com",
     "discovery": True, "default_model": "claude-3-5-haiku-latest", "local": False,
     "capabilities": ["chat", "reasoning", "coding", "research", "summarization",
                      "classification", "vision"]},
    {"id": "openai", "display_name": "OpenAI",
     "description": "GPT models via the OpenAI chat API.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "OpenAI API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.openai.com/v1",
     "discovery": True, "default_model": "gpt-4o-mini", "local": False,
     "capabilities": ["chat", "reasoning", "coding", "research", "summarization",
                      "classification", "vision", "structured_output", "tool_calling"]},
    {"id": "openrouter", "display_name": "OpenRouter",
     "description": "Hundreds of models through one OpenAI-compatible endpoint.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "OpenRouter API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://openrouter.ai/api/v1",
     "discovery": True, "default_model": "openai/gpt-4o-mini", "local": False,
     "capabilities": ["chat", "reasoning", "coding", "research", "summarization",
                      "classification"]},
    {"id": "groq", "display_name": "Groq",
     "description": "Fast inference over an OpenAI-compatible endpoint.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "Groq API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.groq.com/openai/v1",
     "discovery": True, "default_model": "llama-3.1-8b-instant", "local": False,
     "capabilities": ["chat", "coding", "research", "summarization", "classification"]},
    {"id": "deepseek", "display_name": "DeepSeek",
     "description": "DeepSeek chat and reasoning over an OpenAI-compatible endpoint.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "DeepSeek API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.deepseek.com/v1",
     "discovery": True, "default_model": "deepseek-chat", "local": False,
     "capabilities": ["chat", "reasoning", "coding", "research", "summarization",
                      "classification"]},
    {"id": "mistral", "display_name": "Mistral",
     "description": "Mistral models over their OpenAI-compatible endpoint.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "Mistral API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.mistral.ai/v1",
     "discovery": True, "default_model": "mistral-small-latest", "local": False,
     "capabilities": ["chat", "coding", "research", "summarization", "classification"]},
    {"id": "xai", "display_name": "xAI Grok",
     "description": "Grok models over the OpenAI-compatible xAI endpoint.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "xAI API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.x.ai/v1",
     "discovery": True, "default_model": "grok-3-mini", "local": False,
     "capabilities": ["chat", "reasoning", "research", "summarization", "classification"]},
    {"id": "cohere", "display_name": "Cohere",
     "description": "Command models over Cohere's OpenAI-compatible endpoint.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "Cohere API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.cohere.ai/compatibility/v1",
     "discovery": True, "default_model": "command-r", "local": False,
     "capabilities": ["chat", "research", "summarization", "classification"]},
    {"id": "together", "display_name": "Together AI",
     "description": "Open models over Together's OpenAI-compatible endpoint.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "Together API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.together.xyz/v1",
     "discovery": True, "default_model": "", "local": False,
     "capabilities": ["chat", "coding", "research", "summarization", "classification"]},
    {"id": "fireworks", "display_name": "Fireworks AI",
     "description": "Open models over Fireworks' OpenAI-compatible endpoint.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "Fireworks API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.fireworks.ai/inference/v1",
     "discovery": True, "default_model": "", "local": False,
     "capabilities": ["chat", "coding", "research", "summarization", "classification"]},
    {"id": "perplexity", "display_name": "Perplexity",
     "description": "Answer models over Perplexity's OpenAI-compatible endpoint.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "Perplexity API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.perplexity.ai",
     "discovery": True, "default_model": "sonar", "local": False,
     "capabilities": ["chat", "research", "summarization", "classification"]},
    {"id": "google", "display_name": "Google Gemini",
     "description": "Gemini models via the native Generative Language API. Model typed manually.",
     "protocol": "google", "auth": "api_key", "key_required": True,
     "key_label": "Google API Key",
     "endpoint_mode": "fixed",
     "default_endpoint": "https://generativelanguage.googleapis.com",
     "discovery": False, "default_model": "gemini-2.0-flash", "local": False,
     "capabilities": ["chat", "reasoning", "research", "summarization",
                      "classification", "vision"]},
    {"id": "ollama", "display_name": "Ollama (local)",
     "description": "Self-hosted models on this machine or LAN. No key required. "
                    "Installed models are discovered live — never hardcoded.",
     "protocol": "chat", "auth": "optional_key", "key_required": False,
     "key_label": "API Key (optional)",
     "endpoint_mode": "editable", "default_endpoint": "http://127.0.0.1:11434/v1",
     "discovery": True, "default_model": "", "local": True,
     "capabilities": ["chat", "coding", "research", "summarization", "classification"]},
    {"id": "openai-compatible", "display_name": "Custom OpenAI-Compatible",
     "description": "Any OpenAI-compatible chat endpoint (LiteLLM, vLLM, proxies).",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "required", "default_endpoint": "",
     "discovery": True, "default_model": "", "local": False,
     "capabilities": ["chat", "research", "summarization", "classification"]},
    {"id": "responses-compatible", "display_name": "Custom Responses-Compatible",
     "description": "Any endpoint speaking the OpenAI Responses API (/responses).",
     "protocol": "responses", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "required", "default_endpoint": "",
     "discovery": True, "default_model": "", "local": False,
     "capabilities": ["chat", "reasoning", "research", "summarization", "classification"]},
    {"id": "anthropic-compatible", "display_name": "Anthropic-Compatible",
     "description": "Third-party endpoint speaking the Anthropic Messages API.",
     "protocol": "anthropic", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "required", "default_endpoint": "",
     "discovery": True, "default_model": "", "local": False,
     "capabilities": ["chat", "research", "summarization", "classification"]},
    {"id": "google-compatible", "display_name": "Google-Compatible",
     "description": "Third-party endpoint speaking the Gemini API. Model typed manually.",
     "protocol": "google", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "required", "default_endpoint": "",
     "discovery": False, "default_model": "", "local": False,
     "capabilities": ["chat", "research", "summarization", "classification"]},
]

_PROTOCOLS = {"chat", "responses", "anthropic", "google"}

_PROTOCOL_CAPABILITIES = {
    "chat": ["chat", "research", "summarization", "classification"],
    "responses": ["chat", "reasoning", "research", "summarization", "classification"],
    "anthropic": ["chat", "research", "summarization", "classification"],
    "google": ["chat", "research", "summarization", "classification"],
}


def list_presets():
    return [dict(p) for p in PRESETS]


def get_preset(pid: str):
    pid = (pid or "").lower()
    for p in PRESETS:
        if p["id"] == pid:
            return dict(p)
    return None


def valid_protocol(proto: str) -> bool:
    return (proto or "").lower() in _PROTOCOLS


def capabilities_for(preset_id: str = "", protocol: str = "chat"):
    """Adapter-honest capabilities: preset list wins, else protocol default."""
    if preset_id:
        p = get_preset(preset_id)
        if p and p.get("capabilities"):
            return list(p["capabilities"])
    return list(_PROTOCOL_CAPABILITIES.get((protocol or "chat").lower(),
                                           _PROTOCOL_CAPABILITIES["chat"]))


def default_model_for(preset_id: str = "", protocol: str = "chat") -> str:
    if preset_id:
        p = get_preset(preset_id)
        if p:
            return p.get("default_model", "")
    return ""
