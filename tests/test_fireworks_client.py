"""Tests for the Fireworks client wrapper using a fake OpenAI-compatible client.

No SDK, no network: we inject a stub that records calls and can raise a 404 to
exercise the model-fallback path.
"""
import pytest

from app.config import Config
from app.fireworks_client import FireworksError, _fallback_order, complete


class _Message:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Message(content)


class _Response:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class _NotFound(Exception):
    """Stand-in for an OpenAI 404 (model not deployed)."""

    status_code = 404


class FakeClient:
    """Records create() calls; replies per-model from a script."""

    def __init__(self, replies):
        # replies: dict model_id -> str content or Exception to raise
        self._replies = replies
        self.calls = []
        self.chat = self  # allow client.chat.completions.create
        self.completions = self

    def create(self, *, model, messages, temperature, max_tokens):
        self.calls.append(
            {
                "model": model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )
        reply = self._replies[model]
        if isinstance(reply, Exception):
            raise reply
        return _Response(reply)


def _cfg(models):
    return Config(
        api_key="sk-test",
        base_url="https://api.fireworks.ai/inference/v1",
        allowed_models=models,
    )


def test_complete_returns_answer_and_uses_temperature_zero():
    cfg = _cfg(["minimax-m3", "kimi-k2p7-code"])
    fake = FakeClient({"minimax-m3": "Canberra."})
    out = complete(cfg, "Capital of Australia?", preferred_model="minimax-m3", client=fake)
    assert out == "Canberra."
    assert fake.calls[0]["temperature"] == 0
    assert fake.calls[0]["model"] == "minimax-m3"


def test_system_prompt_is_prepended():
    cfg = _cfg(["minimax-m3"])
    fake = FakeClient({"minimax-m3": "ok"})
    complete(cfg, "hi", system="Be concise.", client=fake)
    roles = [m["role"] for m in fake.calls[0]["messages"]]
    assert roles == ["system", "user"]


def test_404_falls_back_to_next_allowed_model():
    cfg = _cfg(["gemma-4-31b-it", "minimax-m3"])
    fake = FakeClient({"gemma-4-31b-it": _NotFound(), "minimax-m3": "fallback answer"})
    out = complete(cfg, "q", preferred_model="gemma-4-31b-it", client=fake)
    assert out == "fallback answer"
    assert [c["model"] for c in fake.calls] == ["gemma-4-31b-it", "minimax-m3"]


def test_all_models_unavailable_raises():
    cfg = _cfg(["gemma-4-31b-it", "gemma-4-26b-a4b-it"])
    fake = FakeClient(
        {"gemma-4-31b-it": _NotFound(), "gemma-4-26b-a4b-it": _NotFound()}
    )
    with pytest.raises(FireworksError):
        complete(cfg, "q", client=fake)


def test_non_404_error_is_wrapped_and_not_retried():
    cfg = _cfg(["minimax-m3", "kimi-k2p7-code"])
    fake = FakeClient({"minimax-m3": ValueError("boom")})
    with pytest.raises(FireworksError):
        complete(cfg, "q", preferred_model="minimax-m3", client=fake)
    # Only the first model was attempted — no retry on a non-availability error.
    assert len(fake.calls) == 1


def test_no_allowed_models_raises():
    with pytest.raises(FireworksError):
        complete(_cfg([]), "q", client=FakeClient({}))


def test_fallback_order_ignores_unlisted_preferred():
    # A preferred model absent from allowed must never be called.
    order = _fallback_order("not-allowed-model", ["minimax-m3", "kimi-k2p7-code"])
    assert order == ["minimax-m3", "kimi-k2p7-code"]


def test_fallback_order_puts_preferred_first_without_duplication():
    order = _fallback_order("kimi-k2p7-code", ["minimax-m3", "kimi-k2p7-code"])
    assert order == ["kimi-k2p7-code", "minimax-m3"]
