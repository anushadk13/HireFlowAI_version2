"""Provider-agnostic LLM client (Gemini, Claude, OpenAI) using a caller-supplied key."""

from __future__ import annotations

import json
import logging
import os
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass

from fastapi import Header

logger = logging.getLogger(__name__)

PROVIDERS = ("gemini", "claude", "openai")
PROVIDER_LABELS = {"gemini": "Gemini", "claude": "Claude", "openai": "OpenAI"}
DEFAULT_MODELS = {
    "gemini": "gemini-3.5-flash-lite",
    "claude": "claude-haiku-5-5",
    "openai": "gpt-4o-mini",
}
REQUEST_TIMEOUT_SECONDS = 60


def _ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


class LLMError(Exception):
    """An AI call failed; the message is safe to show to the user."""


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    api_key: str
    model: str


def resolve_config(provider: str = "", api_key: str = "", model: str = "") -> LLMConfig | None:
    provider = provider.strip().lower()
    api_key = api_key.strip()
    if not api_key:
        # Server-side fallback key (Gemini only), used when the user supplied none.
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        provider = "gemini"
    if not api_key:
        return None
    if provider not in PROVIDERS:
        provider = "gemini"
    return LLMConfig(provider=provider, api_key=api_key, model=model.strip() or DEFAULT_MODELS[provider])


def get_llm_config(
    x_ai_provider: str = Header(default="", alias="X-AI-Provider"),
    x_ai_api_key: str = Header(default="", alias="X-AI-Api-Key"),
    x_ai_model: str = Header(default="", alias="X-AI-Model"),
    x_gemini_api_key: str = Header(default="", alias="X-Gemini-Api-Key"),
) -> LLMConfig | None:
    """FastAPI dependency: the caller's AI settings, or the server's Gemini key, or None."""
    if x_ai_api_key.strip():
        return resolve_config(x_ai_provider, x_ai_api_key, x_ai_model)
    return resolve_config("gemini", x_gemini_api_key, x_ai_model)


def _http_error_message(config: LLMConfig, status: int, body: str) -> str:
    label = PROVIDER_LABELS[config.provider]
    lowered = body.lower()
    if status in (401, 403) or "api key not valid" in lowered or "api_key_invalid" in lowered:
        return f"Your {label} API key was rejected. Check that it is correct and has access."
    if status == 404 or "model" in lowered and "not found" in lowered:
        return f"{label} could not find the model '{config.model}'. Pick a different model."
    if status == 429:
        return f"{label} rate limit or quota exceeded for this API key. Try again later or use another key."
    if status == 400:
        return f"{label} rejected the request (check the model name '{config.model}')."
    return f"{label} returned an error (HTTP {status}). Try again."


def _post_json(config: LLMConfig, url: str, headers: dict[str, str], payload: dict) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS, context=_ssl_context()) as response:  # noqa: S310 - fixed https URLs
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        logger.warning("%s API error %s: %s", config.provider, exc.code, body[:300])
        raise LLMError(_http_error_message(config, exc.code, body)) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        logger.warning("%s API unreachable: %s", config.provider, exc)
        raise LLMError(f"Could not reach {PROVIDER_LABELS[config.provider]}. Check your connection and try again.") from exc


def _generate_gemini(config: LLMConfig, prompt: str, temperature: float, max_tokens: int, json_mode: bool) -> str:
    from google import genai
    from google.genai import errors, types

    try:
        client = genai.Client(api_key=config.api_key)
        response = client.models.generate_content(
            model=config.model,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
                **({"response_mime_type": "application/json"} if json_mode else {}),
            ),
        )
        return response.text or ""
    except errors.APIError as exc:
        logger.warning("gemini API error %s: %s", exc.code, str(exc)[:300])
        raise LLMError(_http_error_message(config, int(exc.code or 0), str(exc))) from exc
    except Exception as exc:  # noqa: BLE001 - network/SDK failures
        logger.warning("gemini call failed: %s", exc)
        raise LLMError("Could not reach Gemini. Check your connection and try again.") from exc


def _generate_claude(config: LLMConfig, prompt: str, temperature: float, max_tokens: int) -> str:
    data = _post_json(
        config,
        "https://api.anthropic.com/v1/messages",
        {"x-api-key": config.api_key, "anthropic-version": "2023-06-01"},
        {
            "model": config.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}],
        },
    )
    return "".join(block.get("text", "") for block in data.get("content", []) if block.get("type") == "text")


def _generate_openai(config: LLMConfig, prompt: str, max_tokens: int, json_mode: bool) -> str:
    payload: dict = {
        "model": config.model,
        "max_completion_tokens": max_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    data = _post_json(
        config,
        "https://api.openai.com/v1/chat/completions",
        {"Authorization": f"Bearer {config.api_key}"},
        payload,
    )
    choices = data.get("choices") or []
    return (choices[0].get("message", {}).get("content") or "") if choices else ""


def generate(
    config: LLMConfig, prompt: str, *, temperature: float = 0, max_tokens: int = 1024, json_mode: bool = False
) -> str:
    if config.provider == "claude":
        return _generate_claude(config, prompt, temperature, max_tokens)
    if config.provider == "openai":
        return _generate_openai(config, prompt, max_tokens, json_mode)
    return _generate_gemini(config, prompt, temperature, max_tokens, json_mode)


def check_config(config: LLMConfig) -> None:
    """Raise LLMError if the key/model can't complete a tiny request."""
    generate(config, "Reply with the single word: ok", max_tokens=16)
