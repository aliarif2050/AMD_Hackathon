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


def test_prompts_preserve_organizer_answer_requirements():
    sentiment = prompts.system_prompt("sentiment").lower()
    assert "mixed" in sentiment
    assert "justify" in sentiment
    assert "both sides" in sentiment

    summary = prompts.system_prompt("summary").lower()
    for constraint in ("sentence", "bullet", "word", "limit"):
        assert constraint in summary

    factual = prompts.system_prompt("factual").lower()
    assert "distinction" in factual
    assert "explanation" in factual

    math = prompts.system_prompt("math").lower()
    assert "every requested result" in math


def test_format_sensitive_prompts_forbid_preamble():
    # C3: preamble/extra text breaks strict-format grading.
    for task_type in ("summary", "factual", "math"):
        assert "preamble" in prompts.system_prompt(task_type).lower()


def test_math_prompt_still_allows_brief_reasoning():
    # C3 must NOT strip the CoT allowance that protects hard multi-hop math.
    assert "justification" in prompts.system_prompt("math").lower()


def test_total_system_prompt_word_budget():
    total_words = sum(len(prompts.system_prompt(task_type).split()) for task_type in TASK_TYPES)
    assert total_words <= 105


def test_category_output_token_limits():
    assert prompts.max_output_tokens("sentiment") == 128
    assert prompts.max_output_tokens("math") == 384
    assert prompts.max_output_tokens("reasoning") == 512
    assert prompts.max_output_tokens("code") == 512
    for task_type in ("factual", "summary", "ner", "general"):
        assert prompts.max_output_tokens(task_type) == 256


def test_unknown_output_limit_falls_back_to_general():
    assert prompts.max_output_tokens("does-not-exist") == 256
