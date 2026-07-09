"""Short, task-specific system prompts (§14.4 / FR-010).

Kept compact to minimise tokens and steer concise English output. No reasoning
traces requested; no PRD/guide text embedded. The user prompt is always the raw
task prompt — these only set the system role.
"""
from __future__ import annotations

_SYSTEM_PROMPTS: dict[str, str] = {
    "general": "Answer accurately and concisely in English.",
    "math": (
        "Solve accurately. Return only the final answer unless a brief reason "
        "is necessary. Answer in English."
    ),
    "sentiment": (
        "Classify the sentiment as positive, negative, neutral, or mixed. "
        "Include one short reason. Answer in English."
    ),
    "summary": "Follow the requested summary format exactly. Be concise. Answer in English.",
    "ner": (
        "Extract named entities with labels. Use a concise 'entity - type' "
        "format. Answer in English."
    ),
    "code": (
        "Return correct code or a concise fix. Avoid unnecessary commentary. "
        "Answer in English."
    ),
    "reasoning": (
        "Solve carefully. Return the final answer with a brief justification. "
        "Answer in English."
    ),
    "factual": "Answer accurately and concisely in English.",
}


def system_prompt(task_type: str) -> str:
    """Return the system prompt for ``task_type`` (falls back to 'general')."""
    return _SYSTEM_PROMPTS.get(task_type, _SYSTEM_PROMPTS["general"])
