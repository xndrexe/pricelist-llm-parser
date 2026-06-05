"""Unit-тест LLM-mapping с моком httpx-клиента.

В CI Ollama нет — поэтому подменяем сетевой клиент детерминированной
заглушкой и проверяем, что наш код корректно разбирает ответ модели.
"""

from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from pricelist_parser.config import Settings
from pricelist_parser.mapping.llm import map_columns_llm


def _make_client(response_body: dict[str, Any], status_code: int = 200) -> httpx.Client:
    """Создаёт httpx.Client с MockTransport, возвращающим заданный ответ."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code=status_code, json=response_body)

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_llm_mapping_parses_clean_json() -> None:
    headers = ["Код 1С", "Номенклатура", "Розница, руб", "На остатке"]
    fake_response = {
        "message": {
            "content": json.dumps(
                {
                    "article": "Код 1С",
                    "name": "Номенклатура",
                    "price": "Розница, руб",
                    "currency": None,
                    "in_stock": "На остатке",
                }
            )
        }
    }
    client = _make_client(fake_response)

    mapping = map_columns_llm(headers, settings=Settings(), client=client)

    assert mapping.article == "Код 1С"
    assert mapping.name == "Номенклатура"
    assert mapping.price == "Розница, руб"
    assert mapping.in_stock == "На остатке"


def test_llm_mapping_ignores_hallucinated_headers() -> None:
    """Если модель выдумала заголовок которого нет — мы его обнуляем."""
    headers = ["SKU", "Title", "Price"]
    fake_response = {
        "message": {
            "content": json.dumps(
                {
                    "article": "SKU",
                    "name": "Title",
                    "price": "Price",
                    "currency": "Несуществующая колонка",
                    "in_stock": None,
                }
            )
        }
    }
    client = _make_client(fake_response)

    mapping = map_columns_llm(headers, settings=Settings(), client=client)

    assert mapping.article == "SKU"
    assert mapping.currency is None


def test_llm_mapping_handles_code_block_wrapping() -> None:
    """Модель иногда оборачивает JSON в ```json ... ``` — парсер должен справиться."""
    headers = ["А", "Н", "Ц"]
    fake_response = {
        "message": {
            "content": "```json\n"
            + json.dumps({"article": "А", "name": "Н", "price": "Ц"})
            + "\n```"
        }
    }
    client = _make_client(fake_response)

    mapping = map_columns_llm(headers, settings=Settings(), client=client)

    assert mapping.article == "А"


def test_llm_mapping_raises_on_no_json() -> None:
    """Если в ответе вообще нет JSON — это явная ошибка, не молча возвращаем пусто."""
    fake_response = {"message": {"content": "Извини, не могу помочь."}}
    client = _make_client(fake_response)

    with pytest.raises(ValueError):
        map_columns_llm(["SKU"], settings=Settings(), client=client)
