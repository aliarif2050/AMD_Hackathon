"""Tests for the runtime configuration loader."""
from app.config import DEFAULT_TIMEOUT, load_config, parse_allowed_models


def test_parse_allowed_models_trims_and_drops_empties():
    raw = " minimax-m3 , kimi-k2p7-code ,, gemma-4-31b-it ,"
    assert parse_allowed_models(raw) == [
        "minimax-m3",
        "kimi-k2p7-code",
        "gemma-4-31b-it",
    ]


def test_parse_allowed_models_handles_none_and_blank():
    assert parse_allowed_models(None) == []
    assert parse_allowed_models("") == []
    assert parse_allowed_models("   ") == []


def test_load_config_reads_all_fields():
    env = {
        "FIREWORKS_API_KEY": "sk-test",
        "FIREWORKS_BASE_URL": "https://api.fireworks.ai/inference/v1",
        "ALLOWED_MODELS": "minimax-m3, kimi-k2p7-code",
    }
    cfg = load_config(env)
    assert cfg.api_key == "sk-test"
    assert cfg.base_url == "https://api.fireworks.ai/inference/v1"
    assert cfg.allowed_models == ["minimax-m3", "kimi-k2p7-code"]
    assert cfg.timeout == DEFAULT_TIMEOUT
    assert cfg.has_fireworks() is True


def test_has_fireworks_false_when_incomplete():
    assert load_config({"ALLOWED_MODELS": "minimax-m3"}).has_fireworks() is False
    assert load_config({"FIREWORKS_API_KEY": "k"}).has_fireworks() is False
    assert load_config({}).has_fireworks() is False


def test_timeout_override_and_bad_values():
    assert load_config({"FIREWORKS_TIMEOUT": "10"}).timeout == 10.0
    assert load_config({"FIREWORKS_TIMEOUT": "nonsense"}).timeout == DEFAULT_TIMEOUT
    assert load_config({"FIREWORKS_TIMEOUT": "-5"}).timeout == DEFAULT_TIMEOUT
