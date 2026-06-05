"""Извлечение строк из .json — случай «нам уже выгрузили почти готовое».

Поддерживаем два разумных варианта структуры:
1. Топ-уровень — массив объектов: `[{...}, {...}]`.
2. Топ-уровень — объект с массивом внутри по ключу `items` / `data` / `rows`.

Всё остальное считаем ошибкой формата — лучше упасть честно, чем
парсить нерегулярную структуру и тихо отдать мусор.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def extract_json(path: Path) -> list[dict[str, Any]]:
    """Загружает JSON и приводит к list[dict].

    Не пытаемся «исправлять» — если структура неожиданная, бросаем ValueError.
    """
    raw = json.loads(path.read_text(encoding="utf-8"))

    if isinstance(raw, list):
        return [item for item in raw if isinstance(item, dict)]

    if isinstance(raw, dict):
        for key in ("items", "data", "rows", "products"):
            inner = raw.get(key)
            if isinstance(inner, list):
                return [item for item in inner if isinstance(item, dict)]

    raise ValueError(
        "Неожиданная структура JSON: ожидался массив объектов или объект "
        "с массивом по ключу items/data/rows/products."
    )
