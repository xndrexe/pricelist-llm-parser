"""LLM-mapping заголовков через локальную Ollama.

Используется, когда эвристика промахнулась — например, на колонках
«Код по 1С», «Розница за упак.», «На остатке шт». Передаём список
заголовков и просим модель вернуть JSON {field → header}. Любая ошибка
сети/парсинга — это сигнал откатиться на эвристику, а не падать наружу.
"""

from __future__ import annotations

import json
import re
from typing import Any

import httpx

from pricelist_parser.config import Settings
from pricelist_parser.schema import ColumnMapping

_SYSTEM_PROMPT = """Ты помогаешь сопоставить заголовки колонок прайс-листа со
стандартной схемой. Тебе дан JSON-массив заголовков. Верни строго JSON-объект
с ключами: article, name, price, currency, in_stock. Значение каждого ключа —
точная строка заголовка из входного списка, либо null, если такого поля нет.
Никаких пояснений, только JSON."""


def _build_user_prompt(headers: list[str]) -> str:
    """Сериализуем заголовки в стабильном виде для повторяемости запросов."""
    return "Заголовки: " + json.dumps(headers, ensure_ascii=False)


def _extract_json_object(text: str) -> dict[str, Any]:
    """Достаёт первый JSON-объект из ответа модели.

    Маленькие instruct-модели иногда оборачивают ответ в ```json ... ``` или
    добавляют комментарий до/после — не наказываем за это, а вырезаем фигурные
    скобки и парсим.
    """
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        raise ValueError("В ответе LLM нет JSON-объекта.")
    return json.loads(match.group(0))  # type: ignore[no-any-return]


def map_columns_llm(
    headers: list[str],
    *,
    settings: Settings | None = None,
    client: httpx.Client | None = None,
) -> ColumnMapping:
    """Отправляет заголовки в Ollama и собирает `ColumnMapping`.

    Параметры `settings`/`client` нужны для тестов с моками. В реальной
    работе вызывающий код передаёт только `headers`, остальное берётся
    из окружения через `Settings()`.
    """
    cfg = settings or Settings()
    owns_client = client is None
    http = client or httpx.Client(timeout=cfg.ollama_timeout_seconds)
    try:
        response = http.post(
            f"{cfg.ollama_host.rstrip('/')}/api/chat",
            json={
                "model": cfg.ollama_model,
                "messages": [
                    {"role": "system", "content": _SYSTEM_PROMPT},
                    {"role": "user", "content": _build_user_prompt(headers)},
                ],
                "stream": False,
                "format": "json",
            },
        )
        response.raise_for_status()
        body = response.json()
        content = body.get("message", {}).get("content", "")
        parsed = _extract_json_object(content)
    finally:
        if owns_client:
            http.close()

    # Оставляем только известные ключи и фильтруем заголовки, которых нет в исходниках —
    # модель иногда выдумывает поля, мы это молча обрезаем.
    allowed_headers = set(headers)
    cleaned: dict[str, str | None] = {}
    for key in ("article", "name", "price", "currency", "in_stock"):
        value = parsed.get(key)
        if isinstance(value, str) and value in allowed_headers:
            cleaned[key] = value
        else:
            cleaned[key] = None
    return ColumnMapping(**cleaned)
