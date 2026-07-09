"""Tests for the classifier and model picker."""
import pytest

from app import router

_CONFIRMED = [
    "minimax-m3",
    "kimi-k2p7-code",
    "gemma-4-31b-it",
    "gemma-4-26b-a4b-it",
    "gemma-4-31b-it-nvfp4",
]


# --------------------------------------------------------------------------- #
# Classification — one representative prompt per category (the official 8 shapes)
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "prompt,expected",
    [
        ("This function has a bug: def get_max(nums): return nums[0]. Fix it.", "code"),
        ("Write a Python function that returns the second-largest number.", "code"),
        ("Summarize the following in exactly one sentence: ...", "summary"),
        ("Classify the sentiment of this review: the battery is great.", "sentiment"),
        ("Extract all named entities and their types from: Maria joined Fireworks.", "ner"),
        ("A store has 240 items. It sells 15% on Monday. How many remain?", "math"),
        ("Three friends each own a different pet. Who owns the cat?", "reasoning"),
        ("What is the capital of Australia?", "factual"),
        ("Tell me something interesting.", "general"),
    ],
)
def test_classify_categories(prompt, expected):
    assert router.classify(prompt) == expected


def test_all_eight_categories_are_reachable():
    # Sanity: the classifier can emit every supported type across a sample set.
    seen = {
        router.classify(p)
        for p in [
            "def f(): pass  # fix bug",
            "Summarize this in one sentence.",
            "What is the sentiment of this review?",
            "Extract all named entities from the text.",
            "The store sold 15% of 240 items, how many remain?",
            "Logic puzzle: three friends each own a pet, who owns the cat?",
            "What is the capital of France?",
            "Say hello.",
        ]
    }
    assert seen == set(router.TASK_TYPES)


# --------------------------------------------------------------------------- #
# Model picker
# --------------------------------------------------------------------------- #

def test_pick_model_code_prefers_kimi():
    assert router.pick_model("code", _CONFIRMED) == "kimi-k2p7-code"


def test_pick_model_factual_prefers_minimax():
    assert router.pick_model("factual", _CONFIRMED) == "minimax-m3"


def test_pick_model_summary_prefers_cheaper_gemma():
    assert router.pick_model("summary", _CONFIRMED) == "gemma-4-26b-a4b-it"


def test_pick_model_never_returns_unlisted_model():
    # kimi absent => code falls to next preferred that IS allowed.
    allowed = ["minimax-m3", "gemma-4-31b-it"]
    chosen = router.pick_model("code", allowed)
    assert chosen in allowed
    assert chosen == "gemma-4-31b-it"


def test_pick_model_heuristic_fallback_on_unknown_names():
    # No confirmed names present => capability heuristic picks a coder for code.
    allowed = ["some-coder-70b", "tiny-chat-3b"]
    assert router.pick_model("code", allowed) == "some-coder-70b"


def test_pick_model_final_fallback_returns_first_allowed():
    allowed = ["mystery-model-x"]
    assert router.pick_model("factual", allowed) == "mystery-model-x"


def test_pick_model_env_override(monkeypatch):
    monkeypatch.setenv("MODEL_OVERRIDE_FACTUAL", "gemma-4-31b-it")
    assert router.pick_model("factual", _CONFIRMED) == "gemma-4-31b-it"


def test_pick_model_override_ignored_when_not_allowed(monkeypatch):
    monkeypatch.setenv("MODEL_OVERRIDE_FACTUAL", "not-in-list")
    # Override absent from allowed => ignored, falls back to preference.
    assert router.pick_model("factual", _CONFIRMED) == "minimax-m3"


def test_pick_model_empty_allowed_raises():
    with pytest.raises(RuntimeError):
        router.pick_model("general", [])
