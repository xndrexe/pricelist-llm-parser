"""Сериализация результата в JSON или CSV.

Намеренно держим форматтеры тонкими: вся очистка и нормализация — слоем
выше, здесь только запись. Это упрощает добавление нового формата
вывода (например, sqlite) — просто новая функция, без рисков для логики.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

from pricelist_parser.schema import ParseResult, PriceListItem

# Колонки CSV-вывода — фиксированный порядок, чтобы импорт в чужие системы
# не ломался от перестановки полей в схеме.
_CSV_FIELDS: list[str] = [
    "article",
    "name",
    "price_rub",
    "currency",
    "in_stock",
    "source_file",
    "row_index",
]


def emit_json(result: ParseResult, path: Path) -> None:
    """Пишет полный `ParseResult` (items + warnings + метаданные).

    JSON — основной формат: сохраняет всю мета-информацию, удобно
    скармливать дальше в API или хранилище.
    """
    path.write_text(
        json.dumps(
            result.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def emit_csv(result: ParseResult, path: Path) -> None:
    """Пишет только items в CSV. Warnings теряются — это осознанно.

    CSV редко используется для дальнейшей машинной обработки внутри
    пайплайна, его обычно открывают в Excel. Тащить туда служебные
    предупреждения смысла нет — они только мешают.
    """
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=_CSV_FIELDS)
        writer.writeheader()
        for item in result.items:
            writer.writerow(_item_to_row(item))


def _item_to_row(item: PriceListItem) -> dict[str, str]:
    """Готовит словарь под `DictWriter`, аккуратно представляя None.

    Excel показывает пустую ячейку как пустую, а строку "None" — как текст.
    Поэтому None превращаем в пустую строку.
    """
    raw = item.model_dump(mode="json")
    return {key: "" if raw.get(key) is None else str(raw[key]) for key in _CSV_FIELDS}
