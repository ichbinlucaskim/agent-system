import pytest

from answer_engine.packaging.app import smoke_test
from answer_engine.packaging.config import ConfigError, load_config
from answer_engine.retrieval import CorpusIndex


def test_config_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ConfigError):
        load_config(require_api_key=True)


def test_smoke(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = load_config(require_api_key=False)
    assert smoke_test(config, CorpusIndex.build(), port=0) == 0
