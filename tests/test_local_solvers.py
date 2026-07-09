from app import fireworks_client, local_solvers, main
from app.config import Config
from app.schema import Task

_ALLOWED = ["minimax-m3", "kimi-k2p7-code", "gemma-4-31b-it", "gemma-4-26b-a4b-it"]


def _live_config():
    return Config(
        api_key="sk-test",
        base_url="https://api.fireworks.ai/inference/v1",
        allowed_models=_ALLOWED,
    )


def test_math_percentage_remaining_answer():
    prompt = "A store has 240 items. It sells 15% on Monday and 60 more on Tuesday. How many items remain?"
    assert local_solvers.try_solve("math", prompt) == "144"


def test_math_explicit_arithmetic_answer():
    assert local_solvers.try_solve("math", "What is 12 * 45?") == "540"
    assert local_solvers.try_solve("math", "What is the sum of 3, 8, and 20?") == "31"


def test_math_declines_ambiguous_word_problem():
    prompt = "A store has 240 red items and 120 blue items. It sells some on Monday. How many remain?"
    assert local_solvers.try_solve("math", prompt) is None


def test_sentiment_one_sided_answers():
    assert local_solvers.try_solve("sentiment", "Classify sentiment: The battery is great and excellent.") == "positive"
    assert local_solvers.try_solve("sentiment", "Classify sentiment: The app is terrible and slow.") == "negative"


def test_sentiment_mixed_or_negated_declines():
    mixed = "Classify the sentiment of this review: The battery life is great, but the screen scratches too easily."
    assert local_solvers.try_solve("sentiment", mixed) is None
    assert local_solvers.try_solve("sentiment", "Classify sentiment: The app is not bad.") is None


def test_ner_is_not_solved_locally():
    prompt = "Extract all named entities and their types from: Maria joined Fireworks AI in Berlin."
    assert local_solvers.try_solve("ner", prompt) is None


def test_solve_returns_local_answer_without_model_call(monkeypatch):
    def _unexpected_call(*a, **k):
        raise AssertionError("Fireworks should not be called for local answers")

    monkeypatch.setattr(fireworks_client, "complete", _unexpected_call)
    answer = main.solve(
        Task(
            task_id="math",
            prompt="A store has 240 items. It sells 15% on Monday and 60 more on Tuesday. How many items remain?",
        ),
        _live_config(),
    )
    assert answer == "144"


def test_solve_falls_through_to_model_when_local_solver_declines(monkeypatch):
    captured = {}

    def _fake_complete(config, prompt, *, system=None, preferred_model=None):
        captured["prompt"] = prompt
        captured["preferred_model"] = preferred_model
        return "model answer"

    monkeypatch.setattr(fireworks_client, "complete", _fake_complete)
    prompt = "Classify the sentiment of this review: The battery is great, but the screen scratches too easily."
    answer = main.solve(Task(task_id="sentiment", prompt=prompt), _live_config())

    assert answer == "model answer"
    assert captured["prompt"] == prompt
    assert captured["preferred_model"] == "gemma-4-26b-a4b-it"
