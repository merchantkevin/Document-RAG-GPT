"""LLM client using the OpenAI-compatible Chat Completions API.

Provider is chosen with the LLM_PROVIDER env var (default: groq). Each provider
reads its own API key env var. The model can be overridden with LLM_MODEL.
"""
import os
from openai import OpenAI

PROVIDERS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "key_env": "GROQ_API_KEY",
        "default_model": "llama-3.3-70b-versatile",
    },
    "openai": {
        "base_url": None,  # SDK default
        "key_env": "OPENAI_API_KEY",
        "default_model": "gpt-4o-mini",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "key_env": "GEMINI_API_KEY",
        "default_model": "gemini-2.0-flash",
    },
}


def _config():
    provider = os.getenv("LLM_PROVIDER", "groq").lower()
    if provider not in PROVIDERS:
        raise ValueError(
            f"Unknown LLM_PROVIDER '{provider}'. Choose from: {', '.join(PROVIDERS)}."
        )
    cfg = PROVIDERS[provider]
    api_key = os.getenv(cfg["key_env"])
    model = os.getenv("LLM_MODEL", cfg["default_model"])
    return cfg, api_key, model


def is_configured() -> bool:
    """True if an API key for the selected provider is present."""
    try:
        _, api_key, _ = _config()
        return bool(api_key)
    except ValueError:
        return False


def _messages(system_prompt, history, user_prompt):
    msgs = [{"role": "system", "content": system_prompt}]
    for m in (history or []):
        role, content = m.get("role"), m.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            msgs.append({"role": role, "content": content})   # drop metadata/options/etc.
    msgs.append({"role": "user", "content": user_prompt})
    return msgs


def generate(system_prompt: str, user_prompt: str, history=None,
             temperature: float = 0.1, max_tokens: int = 700) -> str:
    cfg, api_key, model = _config()
    if not api_key:
        raise RuntimeError(f"Missing API key. Set the {cfg['key_env']} environment variable.")
    client = OpenAI(api_key=api_key, base_url=cfg["base_url"]) if cfg["base_url"] \
        else OpenAI(api_key=api_key)
    resp = client.chat.completions.create(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        messages=_messages(system_prompt, history, user_prompt),
    )
    return (resp.choices[0].message.content or "").strip()
