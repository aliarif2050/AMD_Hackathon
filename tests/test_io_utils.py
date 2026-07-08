import json
from pathlib import Path

import pytest

from app import io_utils
from app.schema import Result, Task


def test_read_tasks_roundtrip(tmp_path: Path):
    p = tmp_path / "tasks.json"
    p.write_text(
        json.dumps([
            {"task_id": "a", "prompt": "one"},
            {"task_id": "b", "prompt": "two"},
        ]),
        encoding="utf-8",
    )
    tasks = io_utils.read_tasks(str(p))
    assert [t.task_id for t in tasks] == ["a", "b"]
    assert isinstance(tasks[0], Task)


def test_read_tasks_rejects_invalid(tmp_path: Path):
    p = tmp_path / "tasks.json"
    p.write_text(json.dumps([{"task_id": "", "prompt": "x"}]), encoding="utf-8")
    with pytest.raises(Exception):
        io_utils.read_tasks(str(p))


def test_write_results_creates_dir_and_file(tmp_path: Path):
    out = tmp_path / "nested" / "results.json"
    results = [Result(task_id="a", answer="A"), Result(task_id="b", answer="B")]
    io_utils.write_results(results, str(out))
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data == [
        {"task_id": "a", "answer": "A"},
        {"task_id": "b", "answer": "B"},
    ]


def test_paths_default_and_override(monkeypatch):
    monkeypatch.delenv("INPUT_PATH", raising=False)
    monkeypatch.delenv("OUTPUT_PATH", raising=False)
    assert io_utils.input_path() == io_utils.DEFAULT_INPUT_PATH
    assert io_utils.output_path() == io_utils.DEFAULT_OUTPUT_PATH
    monkeypatch.setenv("INPUT_PATH", "/tmp/in.json")
    assert io_utils.input_path() == "/tmp/in.json"
