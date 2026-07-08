"""Read the input task file and write the output results file.

Paths default to the container mount points (``/input``, ``/output``) but are
overridable via the ``INPUT_PATH`` / ``OUTPUT_PATH`` env vars for local dev.
Functions take explicit paths so they stay unit-testable.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import TypeAdapter

from app.schema import Result, Task

DEFAULT_INPUT_PATH = "/input/tasks.json"
DEFAULT_OUTPUT_PATH = "/output/results.json"

_TASKS_ADAPTER = TypeAdapter(list[Task])


def input_path() -> str:
    """Resolve the input path (env ``INPUT_PATH`` or the container default)."""
    return os.environ.get("INPUT_PATH", DEFAULT_INPUT_PATH)


def output_path() -> str:
    """Resolve the output path (env ``OUTPUT_PATH`` or the container default)."""
    return os.environ.get("OUTPUT_PATH", DEFAULT_OUTPUT_PATH)


def read_tasks(path: str) -> list[Task]:
    """Load and validate the task list from ``path``."""
    raw = Path(path).read_text(encoding="utf-8")
    data = json.loads(raw)
    return _TASKS_ADAPTER.validate_python(data)


def write_results(results: list[Result], path: str) -> None:
    """Serialize ``results`` to ``path``, creating the parent directory if needed."""
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = [r.model_dump() for r in results]
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
