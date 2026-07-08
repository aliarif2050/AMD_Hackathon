import json
from pathlib import Path

from app import main
from app.schema import Task


def test_run_produces_one_result_per_task(tmp_path: Path):
    in_path = tmp_path / "tasks.json"
    out_path = tmp_path / "results.json"
    in_path.write_text(
        json.dumps([
            {"task_id": "a", "prompt": "one"},
            {"task_id": "b", "prompt": "two"},
        ]),
        encoding="utf-8",
    )

    results = main.run(str(in_path), str(out_path))

    assert [r.task_id for r in results] == ["a", "b"]
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(written) == 2
    assert all(set(item.keys()) == {"task_id", "answer"} for item in written)
    assert all(item["answer"] for item in written)  # non-empty answers


def test_main_returns_zero(tmp_path: Path, monkeypatch):
    in_path = tmp_path / "tasks.json"
    out_path = tmp_path / "results.json"
    in_path.write_text(json.dumps([{"task_id": "a", "prompt": "one"}]), encoding="utf-8")
    monkeypatch.setenv("INPUT_PATH", str(in_path))
    monkeypatch.setenv("OUTPUT_PATH", str(out_path))
    assert main.main() == 0
    assert out_path.exists()


def test_solve_returns_nonempty_string():
    answer = main.solve(Task(task_id="a", prompt="x"))
    assert isinstance(answer, str)
    assert answer
