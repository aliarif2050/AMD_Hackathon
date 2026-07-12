import json
from pathlib import Path

from app import fireworks_client, main
from app.config import Config
from app.schema import Task

_ALLOWED = ["minimax-m3", "kimi-k2p7-code", "gemma-4-31b-it", "gemma-4-26b-a4b-it"]


def _live_config():
    return Config(
        api_key="sk-test",
        base_url="https://api.fireworks.ai/inference/v1",
        allowed_models=_ALLOWED,
    )


def test_run_produces_one_result_per_task(tmp_path: Path, monkeypatch):
    # Mock the Fireworks call so run() exercises the wired pipeline offline.
    monkeypatch.setattr(fireworks_client, "complete", lambda *a, **k: "mocked answer")
    in_path = tmp_path / "tasks.json"
    out_path = tmp_path / "results.json"
    in_path.write_text(
        json.dumps([
            {"task_id": "a", "prompt": "What is the capital of France?"},
            {"task_id": "b", "prompt": "def f(): return 1  # fix this bug"},
        ]),
        encoding="utf-8",
    )

    results = main.run(str(in_path), str(out_path), config=_live_config())

    assert [r.task_id for r in results] == ["a", "b"]
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert len(written) == 2
    assert all(set(item.keys()) == {"task_id", "answer"} for item in written)
    assert all(item["answer"] == "mocked answer" for item in written)


def test_run_falls_back_when_no_fireworks_config(tmp_path: Path):
    # Empty config => solve() raises => per-task fallback, still one result each.
    in_path = tmp_path / "tasks.json"
    out_path = tmp_path / "results.json"
    in_path.write_text(json.dumps([{"task_id": "a", "prompt": "hi"}]), encoding="utf-8")

    results = main.run(str(in_path), str(out_path), config=Config(None, None, []))

    assert results[0].answer == main.FALLBACK_ANSWER


def test_run_falls_back_when_model_call_raises(tmp_path: Path, monkeypatch):
    def _boom(*a, **k):
        raise fireworks_client.FireworksError("all models failed")

    monkeypatch.setattr(fireworks_client, "complete", _boom)
    in_path = tmp_path / "tasks.json"
    out_path = tmp_path / "results.json"
    in_path.write_text(json.dumps([{"task_id": "a", "prompt": "hi"}]), encoding="utf-8")

    results = main.run(str(in_path), str(out_path), config=_live_config())

    assert results[0].answer == main.FALLBACK_ANSWER


def test_main_returns_zero(tmp_path: Path, monkeypatch):
    in_path = tmp_path / "tasks.json"
    out_path = tmp_path / "results.json"
    in_path.write_text(json.dumps([{"task_id": "a", "prompt": "one"}]), encoding="utf-8")
    monkeypatch.setenv("INPUT_PATH", str(in_path))
    monkeypatch.setenv("OUTPUT_PATH", str(out_path))
    # No real creds in env => fallback path, but the batch must still exit 0.
    assert main.main() == 0
    assert out_path.exists()


def test_solve_uses_classified_model_and_returns_answer(monkeypatch):
    captured = {}

    def _fake_complete(config, prompt, *, system=None, preferred_model=None, max_tokens=None):
        captured["preferred_model"] = preferred_model
        captured["system"] = system
        captured["max_tokens"] = max_tokens
        return "Canberra."

    monkeypatch.setattr(fireworks_client, "complete", _fake_complete)
    answer = main.solve(
        Task(task_id="a", prompt="What is the capital of Australia?"),
        _live_config(),
    )
    assert answer == "Canberra."
    # Factual task => minimax-m3 is the top preferred model present in allowed.
    assert captured["preferred_model"] == "minimax-m3"
    assert captured["system"]
    # Phase B: solve must pass the per-category output cap for the classified type.
    from app import prompts

    assert captured["max_tokens"] == prompts.max_output_tokens("factual")
