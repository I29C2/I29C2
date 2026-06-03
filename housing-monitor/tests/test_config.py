import textwrap
from datetime import datetime
from unittest.mock import patch

import pytest

from core.config import Config, ConfigError


def write(tmp_path, text):
    p = tmp_path / "config.yaml"
    p.write_text(textwrap.dedent(text))
    return p


VALID = """
    scheduler:
      interval_minutes: 60
    storage:
      database_path: db.sqlite
    sources:
      - name: WWS Herford
        type: wws_herford
        enabled: true
        url: https://example.com
    filters:
      min_rooms: 3
"""


def test_load_valid(tmp_path):
    cfg = Config.load(write(tmp_path, VALID))
    assert cfg.interval_minutes == 60
    assert cfg.database_path == "db.sqlite"
    assert len(cfg.sources) == 1
    assert cfg.filters["min_rooms"] == 3


def test_missing_file():
    with pytest.raises(ConfigError):
        Config.load("/nonexistent/config.yaml")


def test_bad_interval(tmp_path):
    bad = VALID.replace("interval_minutes: 60", "interval_minutes: 2")
    with pytest.raises(ConfigError):
        Config.load(write(tmp_path, bad))


def test_no_sources(tmp_path):
    bad = """
    scheduler:
      interval_minutes: 60
    sources: []
    """
    with pytest.raises(ConfigError):
        Config.load(write(tmp_path, bad))


def test_source_missing_fields(tmp_path):
    bad = """
    scheduler:
      interval_minutes: 60
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
    with pytest.raises(ConfigError):
        Config.load(write(tmp_path, text))


def test_within_window_true(tmp_path):
    cfg = Config.load(write(tmp_path, VALID))
    # Monday 10:00 → inside window
    fake = datetime(2026, 6, 1, 10, 0)  # Monday
    with patch("core.config.datetime") as mock_dt:
        mock_dt.now.return_value = fake
        assert cfg.within_window() is True


def test_within_window_false_weekend(tmp_path):
    cfg = Config.load(write(tmp_path, VALID))
    fake = datetime(2026, 6, 7, 10, 0)  # Sunday
    with patch("core.config.datetime") as mock_dt:
        mock_dt.now.return_value = fake
        assert cfg.within_window() is False


def test_within_window_false_hour(tmp_path):
    cfg = Config.load(write(tmp_path, VALID))
    fake = datetime(2026, 6, 1, 21, 0)  # Monday but 21:00
    with patch("core.config.datetime") as mock_dt:
        mock_dt.now.return_value = fake
        assert cfg.within_window() is False


def test_save_filters(tmp_path, monkeypatch):
    p = write(tmp_path, VALID)
    cfg = Config.load(p)
    monkeypatch.chdir(tmp_path)
    # copy to config.yaml in tmp_path so save_filters finds it
    (tmp_path / "config.yaml").write_text(p.read_text())
    cfg.save_filters(2, 55)
    assert cfg.raw["filters"]["min_rooms"] == 2
    assert cfg.raw["filters"]["min_area"]  == 55
