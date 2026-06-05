"""Нормализация сырых строк в `PriceListItem`.

Слой берёт «грязный» dict + `ColumnMapping` и выдаёт валидный объект схемы.
Здесь живут разборы чисел («12 345,67» / «12,345.67» / «12345.67»),
определение валюты, очистка артикула, понимание «да/нет/+/-» для наличия.
"""

from __future__ import annotations

import re
from typing import Any

from pricelist_parser.schema import ColumnMapping, Currency, PriceListItem

_TRUE_TOKENS = {"да", "yes", "true", "+", "y", "в наличии", "есть", "1"}
_FALSE_TOKENS = {"нет", "no", "false", "-", "n", "отсутствует", "под заказ", "0"}

# Порядок важен: ловим валютные подсказки внутри значений колонки price или currency.
_CURRENCY_TOKENS: list[tuple[str, Currency]] = [
    ("₽", "RUB"),
    ("руб", "RUB"),
    ("rub", "RUB"),
    ("rur", "RUB"),
    ("$", "USD"),
    ("usd", "USD"),
    ("долл", "USD"),
    ("€", "EUR"),
    ("eur", "EUR"),
    ("евро", "EUR"),
]


def _detect_currency(*values: Any) -> Currency | None:
    """Угадывает валюту по любому из переданных значений.

    Перебираем все значения по очереди — это удобно, когда валюта
    спрятана в строке цены («1 200 руб»), а отдельной колонки валюты нет.
    """
    for value in values:
        if value is None:
            continue
        text = str(value).lower()
        for token, currency in _CURRENCY_TOKENS:
            if token in text:
                return currency
    return None


def parse_price(raw: Any) -> float | None:
    """Разбирает число из произвольной строки или числа.

    Поддерживаем три типичных формата:
    - «12 345,67» — русский с пробелами и запятой,
    - «12,345.67» — англоязычный с запятой как разделитель тысяч,
    - «12345.67»  — простой, и числа `int`/`float` как есть.

    Если на входе мусор — возвращаем None, а не падаем: это позволит
    пайплайну пометить строку warning'ом и продолжить.
    """
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return float(raw)

    text = str(raw).strip()
    # Убираем валютные хвосты и буквы — числовых символов более чем достаточно.
    text = re.sub(r"[^\d.,\-]", "", text)
    if not text:
        return None

    # Случай «12,345.67»: есть и запятая, и точка → запятая = тысячи.
    if "," in text and "." in text:
        text = text.replace(",", "")
    elif "," in text:
        # Решаем, запятая — это десятичный разделитель или тысячи.
        # Если после последней запятой 1-2 цифры — десятичный («12,5», «12,50»),
        # иначе тысячи («12,345» → 12345).
        last_comma = text.rfind(",")
        decimals = text[last_comma + 1 :]
        if len(decimals) in (1, 2) and decimals.isdigit():
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")

    try:
        return float(text)
    except ValueError:
        return None


def _parse_in_stock(raw: Any) -> bool | None:
    """Парсит наличие. None — если не похоже ни на «да», ни на «нет»."""
    if raw is None:
        return None
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return raw > 0

    text = str(raw).strip().lower()
    if not text:
        return None
    if text in _TRUE_TOKENS:
        return True
    if text in _FALSE_TOKENS:
        return False
    # Если в ячейке указано конкретное количество («15 шт»), считаем >0 наличием.
    digits = re.findall(r"\d+", text)
    if digits:
        return int(digits[0]) > 0
    return None


def _clean_article(raw: Any) -> str:
    """Чистит артикул от лишних пробелов и переводов строки.

    Сам артикул может быть числом (Excel хранит 12345 как float) —
    приводим к строке без хвостового «.0».
    """
    if isinstance(raw, float) and raw.is_integer():
        return str(int(raw))
    return str(raw).strip()


def normalize_row(
    row: dict[str, Any],
    mapping: ColumnMapping,
    *,
    source_file: str,
    row_index: int,
) -> tuple[PriceListItem | None, str | None]:
    """Превращает «сырой» dict в `PriceListItem` или возвращает warning.

    Возвращаем кортеж (item, warning), потому что вызывающий код хочет
    положить item в результат, а warning — в `ParseResult.warnings`.
    Если артикул или название пустые — мы не можем сохранить позицию
    осмысленно, поэтому возвращаем (None, "..."). Все остальные
    проблемы (нет цены, неизвестная валюта) — мягкие.
    """
    if mapping.article is None or mapping.name is None:
        return None, f"Строка {row_index}: не определены колонки артикула или названия."

    article_raw = row.get(mapping.article)
    name_raw = row.get(mapping.name)
    if article_raw in (None, "") or name_raw in (None, ""):
        return None, f"Строка {row_index}: пустой артикул или название."

    price_raw = row.get(mapping.price) if mapping.price else None
    currency_raw = row.get(mapping.currency) if mapping.currency else None
    stock_raw = row.get(mapping.in_stock) if mapping.in_stock else None

    price = parse_price(price_raw)
    currency: Currency = _detect_currency(currency_raw, price_raw) or "RUB"

    try:
        item = PriceListItem(
            article=_clean_article(article_raw),
            name=str(name_raw).strip(),
            price_rub=price,
            currency=currency,
            in_stock=_parse_in_stock(stock_raw),
            source_file=source_file,
            row_index=row_index,
        )
    except ValueError as err:
        return None, f"Строка {row_index}: ошибка валидации — {err}"

    warning: str | None = None
    if price is None and price_raw not in (None, ""):
        warning = f"Строка {row_index}: не удалось разобрать цену {price_raw!r}."
    return item, warning
