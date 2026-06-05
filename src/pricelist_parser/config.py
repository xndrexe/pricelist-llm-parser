"""Конфигурация парсера из переменных окружения.

LLM-параметры используются только в режиме `--llm`. В эвристическом
режиме переменные могут отсутствовать — парсер всё равно отработает.
"""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки. Источник — окружение и `.env`, префикс `PRICELIST_`.

    Префикс защищает от пересечения с другими утилитами на машине,
    которые тоже могут смотреть в `OLLAMA_HOST`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="PRICELIST_",
        extra="ignore",
    )

    ollama_host: str = Field(
        default="http://localhost:11434",
        description="Базовый URL локального Ollama-сервера.",
    )
    ollama_model: str = Field(
        default="qwen2.5:7b-instruct",
        description="Имя модели для LLM-разметки колонок.",
    )
    ollama_timeout_seconds: float = Field(
        default=60.0,
        description="Таймаут одного запроса к Ollama. Локальная инференция бывает медленной.",
    )
