"""Batch entrypoint.

Pipeline per task: classify -> pick allowed model -> call Fireworks -> answer.
Config is loaded once at batch start. Every task is wrapped so one failure never
sinks the batch; on any error the per-task fallback answer is written and the
run still exits 0 with one result per input task (the I/O contract).

Local deterministic solvers (Phase 4) will slot in ahead of the Fireworks call
via the marked seam in :func:`solve`.
"""
from __future__ import annotations

import sys

from app import fireworks_client, io_utils, local_solvers, prompts, router
from app.config import Config, load_config
from app.schema import Result, Task

# Fallback used when a single task cannot be answered (per the I/O contract).
FALLBACK_ANSWER = "Unable to determine."


def solve(task: Task, config: Config) -> str:
    """Return an answer for a single task.

    Phase 3: classify -> pick model -> Fireworks. Phase 4 will insert a local
    deterministic solver at the marked seam and only call Fireworks when the
    solver declines (returns None).
    """
    task_type = router.classify(task.prompt)

    local = local_solvers.try_solve(task_type, task.prompt)
    if local is not None:
        return local

    if not config.has_fireworks():
        # No usable runtime config — cannot call the API for this task.
        raise fireworks_client.FireworksError("Fireworks config unavailable")

    model = router.pick_model(task_type, config.allowed_models)
    return fireworks_client.complete(
        config,
        task.prompt,
        system=prompts.system_prompt(task_type),
        preferred_model=model,
        max_tokens=prompts.max_output_tokens(task_type),
    )


def run(in_path: str, out_path: str, config: Config | None = None) -> list[Result]:
    """Read tasks from ``in_path``, answer each, write results to ``out_path``."""
    cfg = config if config is not None else load_config()
    tasks = io_utils.read_tasks(in_path)
    results: list[Result] = []
    for task in tasks:
        try:
            answer = solve(task, cfg)
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
