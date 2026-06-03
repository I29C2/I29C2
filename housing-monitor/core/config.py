"""Configuration loading and validation."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

import yaml


class ConfigError(Exception):
    """Raised when configuration is invalid."""


@dataclass
class Config:
    """Typed view over the YAML config with env-var overrides for secrets."""

    raw: dict

    @classmethod
    def load(cls, path: str | os.PathLike = "config.yaml") -> "Config":
        p = Path(path)
        if not p.exists():
            raise ConfigError(
                f"Config file not found: {p}. Copy config.example.yaml to config.yaml."
            )
        with p.open("r", encoding="utf-8") as fh:
            data = yaml.safe_load(fh) or {}
        cfg = cls(raw=data)
        cfg._apply_env_overrides()
        cfg.validate()
        return cfg

    def _apply_env_overrides(self) -> None:
        tg = self.raw.setdefault("telegram", {})
        if os.getenv("TELEGRAM_BOT_TOKEN"):
            tg["bot_token"] = os.getenv("TELEGRAM_BOT_TOKEN")
        if os.getenv("TELEGRAM_CHAT_ID"):
            tg["chat_id"] = os.getenv("TELEGRAM_CHAT_ID")

    # --- typed accessors ---------------------------------------------------
    def get(self, *keys: str, default: Any = None) -> Any:
        node: Any = self.raw
        for key in keys:
            if not isinstance(node, dict) or key not in node:
                return default
            node = node[key]
        return node

    @property
    def interval_minutes(self) -> int:
        return int(self.get("scheduler", "interval_minutes", default=15))

    @property
    def run_on_start(self) -> bool:
        return bool(self.get("scheduler", "run_on_start", default=True))

    @property
    def database_path(self) -> str:
        return str(self.get("storage", "database_path", default="database/housing.db"))

    @property
    def sources(self) -> list[dict]:
        return [s for s in (self.get("sources", default=[]) or []) if s.get("enabled", True)]

    @property
    def filters(self) -> dict:
        return self.get("filters", default={}) or {}

    @property
    def telegram(self) -> dict:
        return self.get("telegram", default={}) or {}

    @property
    def http(self) -> dict:
        return self.get("http", default={}) or {}

    @property
    def logging(self) -> dict:
        return self.get("logging", default={}) or {}

    @property
    def dashboard(self) -> dict:
        return self.get("dashboard", default={}) or {}

    def validate(self) -> None:
        interval = self.interval_minutes
        if not (5 <= interval <= 1440):
            raise ConfigError(
                f"scheduler.interval_minutes must be between 5 and 1440, got {interval}"
            )
        if not self.sources:
            raise ConfigError("No enabled sources configured under 'sources'.")
        for src in self.sources:
            if "type" not in src or "url" not in src:
                raise ConfigError(f"Source missing 'type' or 'url': {src}")
