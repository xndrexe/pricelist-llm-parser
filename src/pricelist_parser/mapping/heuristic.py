"""Эвристический mapping заголовков по словарю синонимов.

Логика простая: для каждого поля схемы хранится список «индикаторов» —
подстрок, которые встречаются в заголовках реальных прайсов. Сравниваем
заголовок в нижнем регистре, без знаков препинания, и ищем совпадение.
Возвращаем первый подходящий заголовок (приоритет — порядок в списке).
"""

from __future__ import annotations

import re

from pricelist_parser.schema import ColumnMapping

# Порядок внутри списков важен: более точные/специфичные индикаторы первыми.
# Например, «артикул» точнее, чем «код», поэтому идёт раньше.
_SYNONYMS: dict[str, list[str]] = {
    "article": [
        "артикул",
        "sku",
        "код товара",
        "код",
        "vendor code",
        "vendorcode",
        "article",
    ],
    "name": [
        "наименование",
        "название",
        "товар",
        "номенклатура",
        "product",
        "product name",
        "title",
        "name",
    ],
    "price": [
        "цена",
        "стоимость",
        "руб",
        "rub",
        "price",
        "cost",
        "₽",
    ],
    "currency": ["валюта", "currency", "curr"],
    "in_stock": [
        "наличие",
        "в наличии",
        "остаток",
        "склад",
        "stock",
        "in stock",
        "available",
    ],
}


def _normalize(header: str) -> str:
    """Приводит заголовок к канонической форме для сравнения.

    Убираем регистр, лишние пробелы и пунктуацию — иначе «Цена, руб.»
    и «цена руб» считались бы разными.
    """
    lowered = header.lower().strip()
    cleaned = re.sub(r"[^\w\s₽]", " ", lowered, flags=re.UNICODE)
    return re.sub(r"\s+", " ", cleaned).strip()


def map_columns_heuristic(headers: list[str]) -> ColumnMapping:
    """Возвращает `ColumnMapping` для списка заголовков.

    Для каждого поля схемы перебираем синонимы по приоритету. Заголовок,
    в котором встречается синоним как подстрока (после нормализации),
    выигрывает. Один и тот же заголовок не привязываем к двум полям —
    иначе «Цена руб» могло бы попасть и в `price`, и в `currency`.
    """
    normalized = [(original, _normalize(original)) for original in headers]
    used: set[str] = set()
    result: dict[str, str | None] = {}

    for field, indicators in _SYNONYMS.items():
        match: str | None = None
        for indicator in indicators:
            indicator_norm = _normalize(indicator)
            for original, norm in normalized:
                if original in used:
                    continue
                if indicator_norm in norm:
                    match = original
                    break
            if match:
                break
        if match:
            used.add(match)
        result[field] = match

    return ColumnMapping(**result)
