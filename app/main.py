"""Batch entrypoint (Phase 1 skeleton).

Reads tasks, produces a placeholder answer per task, writes results, exits 0.
The placeholder is replaced by deterministic solvers + Fireworks routing in later
phases; this phase only proves the read -> answer -> write pipeline and the I/O contract.
"""
from __future__ import annotations

import sys

from app import io_utils
from app.schema import Result, Task

# Fallback used when a single task cannot be answered (per the I/O contract).
FALLBACK_ANSWER = "Unable to determine."

# Phase 1 placeholder — no solver/model wired yet.
_STUB_ANSWER = "placeholder answer (model not wired yet)"


def solve(task: Task) -> str:
    """Return an answer for a single task. Phase 1: a fixed placeholder."""
    return _STUB_ANSWER


def run(in_path: str, out_path: str) -> list[Result]:
    """Read tasks from ``in_path``, answer each, write results to ``out_path``."""
    tasks = io_utils.read_tasks(in_path)
    results: list[Result] = []
    for task in tasks:
        try:
            answer = solve(task)
        except Exception:  # per-task safety — one bad task never sinks the batch
            answer = FALLBACK_ANSWER
        results.append(Result(task_id=task.task_id, answer=answer))
    io_utils.write_results(results, out_path)
    return results


def main() -> int:
    run(io_utils.input_path(), io_utils.output_path())
    return 0


if __name__ == "__main__":
    sys.exit(main())
