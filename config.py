"""Конфигурация приложения: читается из переменных окружения / .env."""
from __future__ import annotations

from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки бота. Секреты — только из окружения, не хардкодим в коде."""

    bot_token: str
    admin_ids: Annotated[list[int], NoDecode] = []
    notify_interval_min: int = 5
    db_url: str = "sqlite+aiosqlite:///estate.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _parse_admin_ids(cls, value: object) -> list[int]:
        """Разрешаем задавать ADMIN_IDS строкой "111,222"."""
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [int(part.strip()) for part in value.split(",") if part.strip()]
        if isinstance(value, (list, tuple)):
            return [int(v) for v in value]
        return [int(value)]

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids


settings = Settings()
