import textwrap

import pytest

from core.config import Config, ConfigError


def write(tmp_path, text):
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(text))
    return p


VALID = """
    scheduler:
      interval_minutes: 15
    storage:
      database_path: db.sqlite
    sources:
      - name: WWS Herford
        type: wws_herford
        enabled: true
        url: https://example.com
    filters:
      min_rooms: 2
"""


def test_load_valid(tmp_path):
    cfg = Config.load(write(tmp_path, VALID))
    assert cfg.interval_minutes == 15
    assert cfg.database_path == "db.sqlite"
    assert len(cfg.sources) == 1
    assert cfg.filters["min_rooms"] == 2


def test_missing_file():
    with pytest.raises(ConfigError):
        Config.load("/nonexistent/config.yaml")


def test_bad_interval(tmp_path):
    bad = VALID.replace("interval_minutes: 15", "interval_minutes: 2")
    with pytest.raises(ConfigError):
        Config.load(write(tmp_path, bad))


def test_no_sources(tmp_path):
    bad = """
    scheduler:
      interval_minutes: 15
    sources: []
    """
    with pytest.raises(ConfigError):
        Config.load(write(tmp_path, bad))


def test_source_missing_fields(tmp_path):
    bad = """
    scheduler:
      interval_minutes: 15
    sources:
      - name: broken
        enabled: true
    """
    with pytest.raises(ConfigError):
        Config.load(write(tmp_path, bad))


def test_env_overrides(tmp_path, monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")
    cfg = Config.load(write(tmp_path, VALID))
    assert cfg.telegram["bot_token"] == "tok"
    assert cfg.telegram["chat_id"] == "chat"


def test_disabled_sources_excluded(tmp_path):
    text = VALID.replace("enabled: true", "enabled: false")
    # only one source and it's disabled -> validation fails
    with pytest.raises(ConfigError):
        Config.load(write(tmp_path, text))
