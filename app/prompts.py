"""Short, task-specific system prompts (§14.4 / FR-010).

Kept compact to minimise tokens and steer concise English output. No reasoning
traces requested; no PRD/guide text embedded. The user prompt is always the raw
task prompt — these only set the system role.
"""
from __future__ import annotations

_SYSTEM_PROMPTS: dict[str, str] = {
    "general": "Answer accurately and concisely in English.",
    # C3: keep a brief-reason allowance (CoT helps hard multi-hop math the local
    # solver declined) but strip conversational filler ("Sure! Here's...").
    "math": (
        "Solve accurately. Give the final answer, with a brief reason only if "
        "needed. No conversational preamble. Answer in English."
    ),
    "sentiment": (
        "Classify the sentiment as positive, negative, neutral, or mixed. "
        "Include one short reason. Answer in English."
    ),
    # C3: strict-format tasks fail on preamble/extra sentences.
    "summary": (
        "Give only the summary in the exact format requested (for example, "
        "exactly one sentence). No preamble. Answer in English."
    ),
    # C1: NER is graded on completeness + typing — demand ALL entities, define
    # types, and pin a one-per-line format.
    "ner": (
        "Extract ALL named entities. For each, give the entity and its type "
        "(person, organization, location, date, etc.), one per line as "
        "'entity - type'. Answer in English."
    ),
    "code": (
        "Return correct code or a concise fix. Avoid unnecessary commentary. "
        "Answer in English."
    ),
    "reasoning": (
        "Solve carefully. Return the final answer with a brief justification. "
        "Answer in English."
    ),
    # C3: factual answers are format-simple — drop preamble.
    "factual": "Answer accurately and concisely in English. Give only the answer, no preamble.",
}


def system_prompt(task_type: str) -> str:
    """Return the system prompt for ``task_type`` (falls back to 'general')."""
    return _SYSTEM_PROMPTS.get(task_type, _SYSTEM_PROMPTS["general"])


# Phase B token lever: per-category output ceilings (§scoring token rank).
# Each cap clips runaway completions without truncating a typical answer; caps
# for truncation-sensitive tasks (ner/reasoning/code) are kept generous because
# a cut-off answer there loses the accuracy gate. Prompts already steer concise
# output, so this only trims the tail — modest, safe save. Fallback = general.
_OUTPUT_TOKEN_LIMITS: dict[str, int] = {
    "sentiment": 96,
    "factual": 200,
    "summary": 200,
    "general": 256,
    "math": 320,
    "ner": 384,
    "reasoning": 512,
    "code": 512,
}

# Fallback ceiling for any unclassified task type.
_DEFAULT_OUTPUT_LIMIT = 256


def max_output_tokens(task_type: str) -> int:
    """Return the output-token ceiling for ``task_type`` (falls back to default)."""
    return _OUTPUT_TOKEN_LIMITS.get(task_type, _DEFAULT_OUTPUT_LIMIT)
