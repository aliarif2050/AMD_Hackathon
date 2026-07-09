"""Unit tests for the practice-set harness scoring logic (practice/evaluate.py).

These cover the harness's OWN logic (normalization + per-task verdict), not the
80-task run, which stays a manual, zero-API tool. Cases are chosen to be stable
regardless of solver/classifier tuning.
"""
from __future__ import annotations

from practice import evaluate


def test_normalize_lowercases_collapses_and_strips_trailing_punct():
    assert evaluate.normalize("  Positive. ") == "positive"
    assert evaluate.normalize("105 Apples!") == "105 apples"
    assert evaluate.normalize("a   b\tc") == "a b c"
    assert evaluate.normalize("Yes???") == "yes"


def test_accepted_norms_includes_gold_and_variants():
    task = {"gold": "105", "accepted": ["105 apples"]}
    assert evaluate._accepted_norms(task) == {"105", "105 apples"}


def test_score_generative_is_deferred_and_apiless():
    assert evaluate.score_generative({"task_id": "x"}) == "deferred"


def test_math_fire_task_scores_all_green():
    # sum solver reachable via 'sum' keyword; stable under arithmetic tuning.
    task = {
        "task_id": "t-sum",
        "prompt": "What is the sum of 2 and 3?",
        "expected_type": "math",
        "expect_local": True,
        "gold": "5",
        "accepted": ["5"],
    }
    res = evaluate.evaluate_task(task)
    assert res.class_ok and res.fired and res.fire_ok
    assert res.answer_ok is True
    assert res.problems == []


def test_sentiment_decline_task_defers_not_fails():
    task = {
        "task_id": "t-sent",
        "prompt": "Classify the sentiment: It is good, but the wait was slow.",
        "expected_type": "sentiment",
        "expect_local": False,
        "gold": "mixed",
        "accepted": ["mixed", "negative"],
    }
    res = evaluate.evaluate_task(task)
    assert res.class_ok and not res.fired and res.fire_ok
    assert res.deferred is True
    assert res.answer_ok is None
    assert res.problems == []


def test_dangerous_false_fire_is_flagged():
    # If a solver wrongly fires on a task marked expect_local False, it's a miss.
    task = {
        "task_id": "t-falsefire",
        "prompt": "What is the sum of 2 and 3, then explain why?",
        "expected_type": "math",
        "expect_local": False,  # deliberately claim it should decline
        "gold": "5",
    }
    res = evaluate.evaluate_task(task)
    # The sum solver fires -> fire_ok False -> recorded as a problem.
    assert res.fired is True
    assert res.fire_ok is False
    assert any("should decline" in p for p in res.problems)


def test_evaluate_all_and_summarize_shapes():
    tasks = [
        {"task_id": "a", "prompt": "What is the sum of 2 and 3?",
         "expected_type": "math", "expect_local": True, "gold": "5"},
        {"task_id": "b", "prompt": "Summarize this in one sentence: the cat sat.",
         "expected_type": "summary", "expect_local": False, "gold": "cat sat"},
    ]
    evals = evaluate.evaluate_all(tasks)
    cats = evaluate.summarize(evals)
    assert cats["math"]["n"] == 1
    assert cats["summary"]["deferred"] == 1
    # format_report must not raise on a mixed set.
    assert "PRACTICE EVALUATION" in evaluate.format_report(cats, evals)
