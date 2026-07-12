"""Short, task-specific system prompts (§14.4 / FR-010).

Kept compact to minimise tokens and steer concise English output. No reasoning
traces requested; no PRD/guide text embedded. The user prompt is always the raw
task prompt — these only set the system role.
"""
from __future__ import annotations

_SYSTEM_PROMPTS: dict[str, str] = {
    "general": (
        "Answer accurately and concisely in English; follow requested content "
        "and format."
    ),
    "math": (
        "Solve accurately. Include every requested result and a brief "
        "justification if needed. No preamble. English."
    ),
    "sentiment": (
        "Classify as positive, negative, neutral, or mixed. If requested, "
        "briefly justify, covering both sides. English."
    ),
    "summary": (
        "Return only the English summary. Obey exact sentence, bullet, and word "
        "limits; no preamble."
    ),
    "ner": (
        "Extract all named entities and requested types as 'entity - type', "
        "one per line. English."
    ),
    "code": (
        "Return correct, complete code or the requested fix with minimal "
        "English commentary."
    ),
    "reasoning": (
        "Solve carefully. Give every requested result with a brief English "
        "justification."
    ),
    "factual": (
        "Answer accurately and concisely. Include requested distinctions or "
        "explanations; no preamble. English."
    ),
}

_OUTPUT_TOKEN_LIMITS: dict[str, int] = {
    "sentiment": 128,
    "factual": 256,
    "summary": 256,
    "ner": 256,
    "general": 256,
    "math": 384,
    "reasoning": 512,
    "code": 512,
}


def system_prompt(task_type: str) -> str:
    """Return the system prompt for ``task_type`` (falls back to 'general')."""
    return _SYSTEM_PROMPTS.get(task_type, _SYSTEM_PROMPTS["general"])


def max_output_tokens(task_type: str) -> int:
    """Return the conservative output ceiling for ``task_type``."""
    return _OUTPUT_TOKEN_LIMITS.get(task_type, _OUTPUT_TOKEN_LIMITS["general"])
