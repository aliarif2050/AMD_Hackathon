"""Guards for the system prompts, incl. the C1/C3 accuracy-hardening intent.

These lock behavioral intent (NER completeness, no-preamble on format-sensitive
tasks) without over-asserting exact wording, so future tweaks stay easy.
"""
from app import prompts
from app.router import TASK_TYPES


def test_every_task_type_has_a_nonempty_prompt():
    for task_type in TASK_TYPES:
        assert prompts.system_prompt(task_type).strip()


def test_unknown_task_type_falls_back_to_general():
    assert prompts.system_prompt("does-not-exist") == prompts.system_prompt("general")


def test_ner_prompt_demands_all_entities_and_types():
    # C1: completeness + typing are what the judge grades.
    ner = prompts.system_prompt("ner").lower()
    assert "all" in ner
    assert "type" in ner


def test_format_sensitive_prompts_forbid_preamble():
    # C3: preamble/extra text breaks strict-format grading.
    for task_type in ("summary", "factual", "math"):
        assert "preamble" in prompts.system_prompt(task_type).lower()


def test_math_prompt_still_allows_brief_reasoning():
    # C3 must NOT strip the CoT allowance that protects hard multi-hop math.
    assert "reason" in prompts.system_prompt("math").lower()


def test_every_task_type_has_a_positive_output_cap():
    # Phase B: every classifier output must map to a bounded, positive ceiling.
    for task_type in TASK_TYPES:
        assert prompts.max_output_tokens(task_type) > 0


def test_unknown_task_type_output_cap_falls_back():
    # Unclassified tasks still get a sane bounded ceiling.
    assert prompts.max_output_tokens("does-not-exist") == prompts.max_output_tokens("general")


def test_truncation_sensitive_caps_stay_generous():
    # ner/reasoning/code truncation = wrong answer = lost gate point; keep them
    # no smaller than the format-simple categories.
    generous = min(
        prompts.max_output_tokens(t) for t in ("ner", "reasoning", "code")
    )
    assert generous >= prompts.max_output_tokens("sentiment")
