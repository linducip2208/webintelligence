"""Centralized AI provider presets — the single source of truth for the
Add-Provider flow. Frontend renders from GET /api/v1/ai/provider-presets;
backend validates/creates from the same definitions. No duplication.

Every preset maps to a real adapter in factory.build_provider(); no
unsupported providers are listed.
"""
PRESETS = [
    {"id": "opencode-go", "display_name": "OpenCode Go",
     "description": "Muse and curated models through the OpenCode Go gateway (Responses API).",
     "protocol": "responses", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://opencode.ai/zen/go/v1",
     "discovery": True, "default_model": "muse-spark-1.3-contributor", "local": False},
    {"id": "opencode-zen", "display_name": "OpenCode Zen",
     "description": "OpenCode Zen gateway over the OpenAI chat protocol. Endpoint adjustable.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "editable", "default_endpoint": "https://opencode.ai/zen/go/v1",
     "discovery": True, "default_model": "", "local": False},
    {"id": "claude", "display_name": "Claude (Anthropic)",
     "description": "Anthropic Claude via the native Messages API.",
     "protocol": "anthropic", "auth": "api_key", "key_required": True,
     "key_label": "Anthropic API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.anthropic.com",
     "discovery": True, "default_model": "claude-3-5-haiku-latest", "local": False},
    {"id": "openai", "display_name": "OpenAI",
     "description": "GPT models via the OpenAI chat API.",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "OpenAI API Key",
     "endpoint_mode": "fixed", "default_endpoint": "https://api.openai.com/v1",
     "discovery": True, "default_model": "gpt-4o-mini", "local": False},
    {"id": "google", "display_name": "Google Gemini",
     "description": "Gemini models via the native Generative Language API. Model typed manually.",
     "protocol": "google", "auth": "api_key", "key_required": True,
     "key_label": "Google API Key",
     "endpoint_mode": "fixed",
     "default_endpoint": "https://generativelanguage.googleapis.com",
     "discovery": False, "default_model": "gemini-2.0-flash", "local": False},
    {"id": "ollama", "display_name": "Ollama (local)",
     "description": "Self-hosted models on this machine or LAN. No key required.",
     "protocol": "chat", "auth": "optional_key", "key_required": False,
     "key_label": "API Key (optional)",
     "endpoint_mode": "editable", "default_endpoint": "http://127.0.0.1:11434/v1",
     "discovery": True, "default_model": "llama3.1", "local": True},
    {"id": "openai-compatible", "display_name": "Custom OpenAI-Compatible",
     "description": "Any OpenAI-compatible chat endpoint (LiteLLM, vLLM, proxies).",
     "protocol": "chat", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "required", "default_endpoint": "",
     "discovery": True, "default_model": "", "local": False},
    {"id": "responses-compatible", "display_name": "Custom Responses-Compatible",
     "description": "Any endpoint speaking the OpenAI Responses API (/responses).",
     "protocol": "responses", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "required", "default_endpoint": "",
     "discovery": True, "default_model": "", "local": False},
    {"id": "anthropic-compatible", "display_name": "Anthropic-Compatible",
     "description": "Third-party endpoint speaking the Anthropic Messages API.",
     "protocol": "anthropic", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "required", "default_endpoint": "",
     "discovery": True, "default_model": "", "local": False},
    {"id": "google-compatible", "display_name": "Google-Compatible",
     "description": "Third-party endpoint speaking the Gemini API. Model typed manually.",
     "protocol": "google", "auth": "api_key", "key_required": True,
     "key_label": "API Key",
     "endpoint_mode": "required", "default_endpoint": "",
     "discovery": False, "default_model": "", "local": False},
]

_PROTOCOLS = {"chat", "responses", "anthropic", "google"}


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
