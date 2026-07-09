"""Task-type classification and allowed-model selection.

Two pieces (both deterministic, zero-token):

* :func:`classify` — keyword/heuristic classifier mapping a prompt to one of the
  eight supported task types (FR-008). Cheap and explainable; the fine-tuned
  router (Phase 7a) can later replace it while keeping this as the fallback.
* :func:`pick_model` — returns the best model for a task type that is present in
  the runtime ``ALLOWED_MODELS`` (§14.3). Explicit preference first, capability
  heuristic as fallback. **Never returns a model absent from ``allowed``.**
"""
from __future__ import annotations

import os
import re

# Supported task types (FR-008). "general" is the safe default.
TASK_TYPES = (
    "math",
    "sentiment",
    "ner",
    "summary",
    "code",
    "reasoning",
    "factual",
    "general",
)

# --------------------------------------------------------------------------- #
# Classification
# --------------------------------------------------------------------------- #

_CODE_HINTS = (
    "def ",
    "function",
    "code",
    "bug",
    "debug",
    "fix",
    "python",
    "javascript",
    "return ",
    "compile",
    "algorithm",
    "regex",
    "stack trace",
    "traceback",
)
_SENTIMENT_HINTS = (
    "sentiment",
    "positive or negative",
    "positive, negative",
    "how do they feel",
    "tone of",
)
_NER_HINTS = (
    "named entit",
    "entities",
    "extract all",
    "entity type",
    "extract the names",
    "identify the people",
)
_SUMMARY_HINTS = (
    "summarize",
    "summarise",
    "summary",
    "in one sentence",
    "in a sentence",
    "tl;dr",
    "condense",
    "in exactly one sentence",
)
_REASONING_HINTS = (
    "puzzle",
    "each own",
    "who owns",
    "logic",
    "if and only if",
    "deduce",
    "constraint",
    "how many ways",
    "which one",
    "true or false",
)
_FACTUAL_HINTS = (
    "what is",
    "who is",
    "where is",
    "when did",
    "capital of",
    "define",
    "definition of",
    "explain",
    "how many",
)

_MATH_KEYWORDS = (
    "percent",
    "%",
    "sum",
    "average",
    "remain",
    "how much",
    "total",
    "multiply",
    "divide",
    "difference",
    "product of",
)


def _has_math_shape(text: str) -> bool:
    """True when the prompt looks like a numeric computation problem."""
    if "%" in text:
        return True
    # Two or more standalone numbers plus a math keyword => likely word problem.
    numbers = re.findall(r"\b\d+(?:\.\d+)?\b", text)
    if len(numbers) >= 2 and any(k in text for k in _MATH_KEYWORDS):
        return True
    return False


def _any(text: str, hints: tuple[str, ...]) -> bool:
    return any(h in text for h in hints)


def classify(prompt: str) -> str:
    """Classify ``prompt`` into one of :data:`TASK_TYPES`.

    Deterministic keyword heuristic. Order matters: the most specific,
    format-sensitive categories (code, ner, sentiment, summary) are checked
    before the broader ones (math, reasoning, factual), and ``general`` is the
    catch-all.
    """
    text = prompt.lower()

    # Code is highly signalled (syntax tokens) and format-sensitive.
    if _any(text, _CODE_HINTS):
        return "code"
    # NER before sentiment/summary — "extract entities" is unambiguous.
    if _any(text, _NER_HINTS):
        return "ner"
    if _any(text, _SENTIMENT_HINTS):
        return "sentiment"
    if _any(text, _SUMMARY_HINTS):
        return "summary"
    if _has_math_shape(text):
        return "math"
    if _any(text, _REASONING_HINTS):
        return "reasoning"
    if _any(text, _FACTUAL_HINTS):
        return "factual"
    return "general"


# --------------------------------------------------------------------------- #
# Model selection (§14.3)
# --------------------------------------------------------------------------- #

# Explicit preference tuned to the CONFIRMED Track 1 models (§10.4).
# Used only to RANK; always filtered against runtime ALLOWED_MODELS.
_PREFERENCES: dict[str, list[str]] = {
    "code": ["kimi-k2p7-code", "gemma-4-31b-it", "minimax-m3"],
    "reasoning": ["minimax-m3", "gemma-4-31b-it", "kimi-k2p7-code"],
    "factual": ["minimax-m3", "gemma-4-31b-it", "gemma-4-26b-a4b-it"],
    "summary": ["gemma-4-26b-a4b-it", "gemma-4-31b-it-nvfp4", "gemma-4-31b-it"],
    "sentiment": ["gemma-4-26b-a4b-it", "gemma-4-31b-it-nvfp4", "minimax-m3"],
    "ner": ["gemma-4-31b-it", "gemma-4-26b-a4b-it", "minimax-m3"],
    "math": ["minimax-m3", "gemma-4-31b-it", "kimi-k2p7-code"],
    "general": ["minimax-m3", "gemma-4-31b-it", "gemma-4-26b-a4b-it"],
}


def _tags(model_id: str) -> set[str]:
    """Capability tags inferred from a model name (heuristic fallback)."""
    m = model_id.lower()
    tags: set[str] = set()
    if any(k in m for k in ("code", "coder", "kimi")):
        tags.add("code")
    if any(k in m for k in ("instruct", "-it", "chat", "gemma", "minimax")):
        tags.add("instruct")
    sizes = [int(n) for n in re.findall(r"(\d+)\s*b", m)]
    tags.add("large" if (max(sizes) if sizes else 0) >= 30 else "small")
    return tags


_TAG_PREFS: dict[str, list[tuple[str, ...]]] = {
    "code": [("code",), ("instruct", "large"), ("instruct",)],
    "reasoning": [("instruct", "large"), ("code",), ("instruct",)],
    "factual": [("instruct", "large"), ("instruct",)],
    "summary": [("instruct",)],
    "sentiment": [("instruct",)],
    "ner": [("instruct",)],
    "math": [("instruct", "large"), ("instruct",)],
    "general": [("instruct", "large"), ("instruct",)],
}


def pick_model(task_type: str, allowed: list[str]) -> str:
    """Return the best model for ``task_type`` that is present in ``allowed``.

    Order: launch-day override (if allowed) → explicit preference (§10.4) →
    capability heuristic → first allowed model. Never returns a model absent
    from ``allowed``.
    """
    if not allowed:
        raise RuntimeError("No allowed models available")

    # Optional launch-day override: MODEL_OVERRIDE_<TASKTYPE>=<model_id>
    override = os.environ.get(f"MODEL_OVERRIDE_{task_type.upper()}")
    if override and override in allowed:
        return override

    # Primary: explicit preference tuned to confirmed models.
    for candidate in _PREFERENCES.get(task_type, _PREFERENCES["general"]):
        if candidate in allowed:
            return candidate

    # Fallback: capability heuristic over whatever names are present.
    scored = [(m, _tags(m)) for m in allowed]
    for wanted in _TAG_PREFS.get(task_type, _TAG_PREFS["general"]):
        want = set(wanted)
        for model_id, tags in scored:
            if want.issubset(tags):
                return model_id

    return allowed[0]  # final fallback — never call an unlisted model
