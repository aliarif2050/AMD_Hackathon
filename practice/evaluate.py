"""Standalone, zero-API evaluator for the deterministic layer (PRD §21, Phase 6).

Scores the shipped router + local solvers against ``practice/eval_set.json``
WITHOUT ever calling Fireworks. Three dimensions per task:

1. **classification** — ``router.classify(prompt) == expected_type``.
2. **solver targeting** — a local solver fired (non-``None``) *iff* ``expect_local``
   is true. This uses PRODUCTION routing: ``try_solve(classified_type, prompt)`` —
   the solver only ever sees the type the classifier chose, exactly as in
   ``main.solve``. So a misclassification that starves a solver shows up here.
3. **answer-match** — for ``expect_local`` tasks, the normalized solver output is
   one of the normalized accepted variants (``gold`` + ``accepted``).

Model-routed tasks (``expect_local == false``) are not answer-scored today; the
deferred generative seam :func:`score_generative` returns ``"deferred"`` for them
(a stub for a later local/Groq generative layer — see D-6). Never calls an API.

Run:  ``python practice/evaluate.py``   (or ``python -m practice.evaluate``)
"""
from __future__ import annotations

import json
import os
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field

# Make the repo root importable when run as a plain script (sys.path[0] would
# otherwise be practice/, hiding the top-level ``app`` package).
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from app import local_solvers, router  # noqa: E402  (after sys.path shim)

EVAL_SET = os.path.join(os.path.dirname(os.path.abspath(__file__)), "eval_set.json")

_CATEGORY_ORDER = (
    "math",
    "sentiment",
    "reasoning",
    "code",
    "ner",
    "summary",
    "factual",
    "general",
)


# --------------------------------------------------------------------------- #
# Normalization + generative seam
# --------------------------------------------------------------------------- #
def normalize(text: str) -> str:
    """Lowercase, collapse whitespace, strip trailing punctuation (D-4).

    Mirrors the meaning-based judge just enough to avoid false failures on
    casing/spacing/trailing punctuation, without over-normalizing content.
    """
    text = re.sub(r"\s+", " ", text.strip().lower())
    return re.sub(r"[.!?]+$", "", text).strip()


def score_generative(task: dict) -> str:
    """Deferred seam for a later generative layer (D-6). Never calls an API."""
    return "deferred"


def _accepted_norms(task: dict) -> set[str]:
    variants = list(task.get("accepted") or [])
    if task.get("gold"):
        variants.append(task["gold"])
    return {normalize(v) for v in variants if v}


# --------------------------------------------------------------------------- #
# Per-task evaluation
# --------------------------------------------------------------------------- #
@dataclass
class TaskEval:
    task_id: str
    category: str
    expected_type: str
    classified: str
    class_ok: bool
    expect_local: bool
    fired: bool
    fire_ok: bool
    answer: str | None            # solver output when it fired, else None
    answer_ok: bool | None        # None => not applicable (declined / deferred)
    deferred: bool
    classifier_masked_solver: bool  # solver WOULD have fired on the correct type
    problems: list[str] = field(default_factory=list)


def evaluate_task(task: dict) -> TaskEval:
    prompt = task["prompt"]
    expected = task["expected_type"]
    expect_local = bool(task.get("expect_local", False))
    category = task.get("category", expected)

    classified = router.classify(prompt)
    class_ok = classified == expected

    # Production routing: the solver only sees the CLASSIFIED type.
    answer = local_solvers.try_solve(classified, prompt)
    fired = answer is not None
    fire_ok = fired == expect_local

    # Diagnostic: would a solver have fired if the classifier had been correct?
    solved_expected = local_solvers.try_solve(expected, prompt)
    classifier_masked_solver = expect_local and not fired and solved_expected is not None

    answer_ok: bool | None = None
    deferred = False
    problems: list[str] = []

    if not class_ok:
        problems.append(f"class: got '{classified}', want '{expected}'")
    if not fire_ok:
        if expect_local:
            problems.append("solver: stayed silent, should fire")
        else:
            problems.append(f"solver: fired (={answer!r}), should decline")

    if expect_local and fired:
        answer_ok = normalize(answer) in _accepted_norms(task)
        if not answer_ok:
            problems.append(
                f"answer: got {answer!r}, want one of {sorted(_accepted_norms(task))}"
            )
    elif not expect_local:
        # Model-routed: deferred to the generative layer (not a failure today).
        deferred = score_generative(task) == "deferred"

    return TaskEval(
        task_id=task["task_id"],
        category=category,
        expected_type=expected,
        classified=classified,
        class_ok=class_ok,
        expect_local=expect_local,
        fired=fired,
        fire_ok=fire_ok,
        answer=answer,
        answer_ok=answer_ok,
        deferred=deferred,
        classifier_masked_solver=classifier_masked_solver,
        problems=problems,
    )


def evaluate_all(tasks: list[dict]) -> list[TaskEval]:
    return [evaluate_task(t) for t in tasks]


# --------------------------------------------------------------------------- #
# Aggregation + reporting
# --------------------------------------------------------------------------- #
def summarize(evals: list[TaskEval]) -> dict[str, dict[str, int]]:
    cats: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "n": 0,
            "class_ok": 0,
            "fire_ok": 0,
            "ans_n": 0,
            "ans_ok": 0,
            "deferred": 0,
        }
    )
    for e in evals:
        c = cats[e.category]
        c["n"] += 1
        c["class_ok"] += int(e.class_ok)
        c["fire_ok"] += int(e.fire_ok)
        if e.expect_local and e.fired:
            c["ans_n"] += 1
            c["ans_ok"] += int(bool(e.answer_ok))
        if e.deferred:
            c["deferred"] += 1
    return cats


def _pct(ok: int, n: int) -> str:
    return f"{100 * ok / n:5.1f}%" if n else "   n/a"


def format_report(cats: dict[str, dict[str, int]], evals: list[TaskEval]) -> str:
    lines = [
        "=" * 78,
        "PRACTICE EVALUATION — deterministic layer (zero API)",
        "=" * 78,
        f"{'category':10} {'n':>3} {'class':>7} {'fire':>7} {'answer':>9} {'deferred':>9}",
        "-" * 78,
    ]
    totals: dict[str, int] = defaultdict(int)
    for cat in _CATEGORY_ORDER:
        if cat not in cats:
            continue
        c = cats[cat]
        ans = f"{c['ans_ok']}/{c['ans_n']}" if c["ans_n"] else "-"
        lines.append(
            f"{cat:10} {c['n']:>3} {_pct(c['class_ok'], c['n']):>7} "
            f"{_pct(c['fire_ok'], c['n']):>7} {ans:>9} {c['deferred']:>9}"
        )
        for k, v in c.items():
            totals[k] += v
    lines.append("-" * 78)
    tans = f"{totals['ans_ok']}/{totals['ans_n']}" if totals["ans_n"] else "-"
    lines.append(
        f"{'TOTAL':10} {totals['n']:>3} {_pct(totals['class_ok'], totals['n']):>7} "
        f"{_pct(totals['fire_ok'], totals['n']):>7} {tans:>9} {totals['deferred']:>9}"
    )
    lines.append("=" * 78)

    misses = [e for e in evals if e.problems]
    lines.append(f"MISSES: {len(misses)} of {len(evals)}")
    for e in misses:
        tail = "  (classifier masked solver)" if e.classifier_masked_solver else ""
        lines.append(f"  [{e.task_id}] " + "; ".join(e.problems) + tail)
    return "\n".join(lines)


def _report_payload(cats, evals) -> dict:
    return {
        "totals": {
            "tasks": len(evals),
            "class_ok": sum(c["class_ok"] for c in cats.values()),
            "fire_ok": sum(c["fire_ok"] for c in cats.values()),
            "answer_ok": sum(c["ans_ok"] for c in cats.values()),
            "answer_n": sum(c["ans_n"] for c in cats.values()),
            "deferred": sum(c["deferred"] for c in cats.values()),
            "misses": sum(1 for e in evals if e.problems),
        },
        "by_category": {k: dict(v) for k, v in cats.items()},
        "misses": [
            {"task_id": e.task_id, "problems": e.problems,
             "classifier_masked_solver": e.classifier_masked_solver}
            for e in evals if e.problems
        ],
    }


def main(path: str = EVAL_SET) -> int:
    with open(path, encoding="utf-8") as fh:
        tasks = json.load(fh)
    evals = evaluate_all(tasks)
    cats = summarize(evals)
    print(format_report(cats, evals))

    out = os.path.join(os.path.dirname(os.path.abspath(path)), "eval_report.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(_report_payload(cats, evals), fh, indent=2)
    print(f"\nWrote machine-readable report -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
