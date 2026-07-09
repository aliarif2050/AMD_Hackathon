"""Thin OpenAI-compatible wrapper around the Fireworks chat API.

Policy (PRD §14.5): ``temperature=0``, per-request timeout, no streaming, no
runaway retries. The only retry we perform is a **model fallback on 404** — an
allowed-but-not-deployed model (e.g. on-demand Gemma) returns 404, so we move to
the next model in the runtime ``ALLOWED_MODELS`` list rather than failing the
task. Every model tried is filtered against ``ALLOWED_MODELS``; we never call an
unlisted model.
"""
from __future__ import annotations

from typing import Any

from app.config import Config

# Default output ceiling. Task-type specific caps come with the Phase 3 router;
# this keeps single calls bounded and cheap by default.
DEFAULT_MAX_TOKENS = 512


class FireworksError(RuntimeError):
    """Raised when a chat completion cannot be produced from any allowed model."""


def _is_model_unavailable(exc: Exception) -> bool:
    """Heuristically detect a 404 / model-not-deployed error, client-agnostic."""
    status = getattr(exc, "status_code", None) or getattr(exc, "status", None)
    if status == 404:
        return True
    text = str(exc).lower()
    return "not found" in text or "not deployed" in text or "404" in text


def build_client(config: Config) -> Any:
    """Construct an OpenAI-compatible client pointed at Fireworks.

    Imported lazily so unit tests can inject a fake client without the SDK, and
    so import cost is only paid when a real call is needed.
    """
    from openai import OpenAI

    return OpenAI(
        api_key=config.api_key,
        base_url=config.base_url,
        timeout=config.timeout,
    )


def _fallback_order(preferred: str | None, allowed: list[str]) -> list[str]:
    """Ordered, de-duplicated list of models to try, all within ``allowed``.

    ``preferred`` (if present in ``allowed``) is tried first, then the remaining
    allowed models in their runtime order. A ``preferred`` not in ``allowed`` is
    ignored — we never call an unlisted model.
    """
    order: list[str] = []
    if preferred and preferred in allowed:
        order.append(preferred)
    for model in allowed:
        if model not in order:
            order.append(model)
    return order


def complete(
    config: Config,
    prompt: str,
    *,
    system: str | None = None,
    preferred_model: str | None = None,
    max_tokens: int = DEFAULT_MAX_TOKENS,
    client: Any | None = None,
) -> str:
    """Return the model's answer text for ``prompt``.

    Tries ``preferred_model`` first, then falls back through the remaining
    ``ALLOWED_MODELS`` on a 404 (model not deployed). Raises
    :class:`FireworksError` if no allowed model can answer.
    """
    if not config.allowed_models:
        raise FireworksError("No allowed models available")

    api = client if client is not None else build_client(config)

    messages: list[dict[str, str]] = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    last_error: Exception | None = None
    for model in _fallback_order(preferred_model, config.allowed_models):
        try:
            response = api.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                max_tokens=max_tokens,
            )
        except Exception as exc:  # noqa: BLE001 — classify then decide
            last_error = exc
            if _is_model_unavailable(exc):
                continue  # try the next allowed model
            raise FireworksError(f"Fireworks call failed: {exc}") from exc

        content = response.choices[0].message.content
        if content and content.strip():
            return content.strip()
        last_error = FireworksError(f"Empty response from {model}")

    raise FireworksError(
        f"All allowed models failed; last error: {last_error}"
    )
