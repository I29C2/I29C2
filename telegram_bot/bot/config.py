# telegram_bot/bot/config.py
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    TELEGRAM_BOT_TOKEN: str = field(
        default_factory=lambda: os.environ.get("TELEGRAM_BOT_TOKEN", "")
    )
    BACKEND_API_URL: str = field(
        default_factory=lambda: os.environ.get("BACKEND_API_URL", "http://backend:8000")
    )

    def __post_init__(self) -> None:
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")


config = Config()
