"""Packaging: config and smoke without a model call."""

from __future__ import annotations

import os

import pytest

from support_desk.packaging.config import ConfigError, load_config
from support_desk.packaging.app import smoke_test


def test_load_config_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    with pytest.raises(ConfigError):
        load_config(require_api_key=True)


def test_load_config_offline_ok(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = load_config(require_api_key=False)
    assert config.api_key == "offline"


def test_smoke_health(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    config = load_config(require_api_key=False)
    assert smoke_test(config, port=0) == 0
