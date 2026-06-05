"""Pydantic-схемы выходного формата и промежуточных контрактов.

`PriceListItem` — единый формат, к которому мы приводим любой вход.
`ColumnMapping` — результат шага «определить, какая колонка что значит».
`ParseResult` — пакет {items, warnings, source_meta}, чтобы CLI мог
показать пользователю, что прошло гладко, а что было домыслено.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# Поддерживаемые валюты. Литерал, а не enum — чтобы JSON выглядел естественно
# и схема легко переиспользовалась из других сервисов без импорта enum-класса.
Currency = Literal["RUB", "USD", "EUR"]


class PriceListItem(BaseModel):
    """Одна строка нормализованного прайс-листа.

    Артикул и название — обязательны. Цена опциональна, потому что в реальных
    выгрузках встречаются строки «уточняйте» или пустые ячейки, и терять такие
    позиции жалко — лучше вернуть `price_rub=None` и пометить в warnings.
    """

    model_config = ConfigDict(str_strip_whitespace=True)

    article: str = Field(..., min_length=1, description="Артикул/SKU/код товара.")
    name: str = Field(..., min_length=1, description="Наименование товара.")
    price_rub: float | None = Field(
        default=None,
        ge=0,
        description="Цена в рублях (после конвертации из исходной валюты).",
    )
    currency: Currency = Field(
        default="RUB",
        description="Исходная валюта строки. Цена уже пересчитана в RUB.",
    )
    in_stock: bool | None = Field(
        default=None,
        description="Наличие на складе. None, если в исходнике нет такой колонки.",
    )
    source_file: str = Field(..., description="Имя исходного файла для отслеживания.")
    row_index: int = Field(..., ge=0, description="Номер строки в исходнике (0-индекс).")


class ColumnMapping(BaseModel):
    """Соответствие заголовков исходного файла полям `PriceListItem`.

    Значения — оригинальные строки заголовков. Если поле не найдено в
    исходнике — оно отсутствует в словаре (а не None), чтобы было легче
    отличить «нет такой колонки» от «есть, но пустая».
    """

    article: str | None = None
    name: str | None = None
    price: str | None = None
    currency: str | None = None
    in_stock: str | None = None


class ParseResult(BaseModel):
    """Результат полного прогона пайплайна.

    `warnings` — мягкие проблемы, не блокирующие выдачу: «строка 14 без цены»,
    «валюту угадать не удалось, считаю RUB». Критические ошибки кидаются
    исключениями и до `ParseResult` не доходят.
    """

    items: list[PriceListItem]
    warnings: list[str] = Field(default_factory=list)
    source_file: str
    rows_total: int = Field(..., ge=0, description="Сколько строк было в исходнике.")
    rows_kept: int = Field(..., ge=0, description="Сколько строк попало в items.")
