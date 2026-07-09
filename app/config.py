"""Runtime configuration loaded from harness-injected environment variables.

The grading harness injects ``FIREWORKS_API_KEY``, ``FIREWORKS_BASE_URL`` and
``ALLOWED_MODELS`` at runtime. Nothing here is ever hardcoded: model IDs come
only from the runtime ``ALLOWED_MODELS`` value, and secrets are read from the
environment (never committed, never cached).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

# Default per-request timeout (seconds). Kept under the harness <30s/request
# budget with margin. Overridable via FIREWORKS_TIMEOUT for local tuning.
DEFAULT_TIMEOUT = 25.0


def parse_allowed_models(raw: str | None) -> list[str]:
    """Split a comma-separated ``ALLOWED_MODELS`` string into clean model IDs.

    Trims whitespace around each entry and drops empties. Order is preserved
    (it carries no meaning for us — the picker ranks explicitly). Returns an
    empty list when the variable is unset or blank.
    """
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


@dataclass(frozen=True)
class Config:
    """Immutable snapshot of runtime configuration."""

    api_key: str | None
    base_url: str | None
    allowed_models: list[str] = field(default_factory=list)
    timeout: float = DEFAULT_TIMEOUT

    def has_fireworks(self) -> bool:
        """True when we have the minimum needed to call Fireworks."""
        return bool(self.api_key and self.base_url and self.allowed_models)


def _parse_timeout(raw: str | None) -> float:
    """Parse FIREWORKS_TIMEOUT, falling back to the default on any bad value."""
    if not raw:
        return DEFAULT_TIMEOUT
    try:
        value = float(raw)
    except ValueError:
        return DEFAULT_TIMEOUT
    return value if value > 0 else DEFAULT_TIMEOUT


def load_config(env: dict[str, str] | None = None) -> Config:
    """Build a :class:`Config` from the environment (or an injected mapping).

    ``env`` defaults to ``os.environ``; passing an explicit mapping keeps this
    unit-testable without mutating process state.
    """
    source = os.environ if env is None else env
    return Config(
        api_key=source.get("FIREWORKS_API_KEY"),
        base_url=source.get("FIREWORKS_BASE_URL"),
        allowed_models=parse_allowed_models(source.get("ALLOWED_MODELS")),
        timeout=_parse_timeout(source.get("FIREWORKS_TIMEOUT")),
    )
