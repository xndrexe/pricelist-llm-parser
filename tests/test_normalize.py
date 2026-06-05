"""Тесты нормализации: разбор чисел, валют, наличия."""

from __future__ import annotations

import pytest

from pricelist_parser.normalize import normalize_row, parse_price
from pricelist_parser.schema import ColumnMapping


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("12 345,67", 12345.67),
        ("12345.67", 12345.67),
        ("12,345.67", 12345.67),
        ("1 250,50", 1250.50),
        ("350,00", 350.00),
        ("350.00", 350.00),
        ("12 345", 12345.0),
        ("12,5", 12.5),
        ("1 200 руб", 1200.0),
        (1500, 1500.0),
        (1500.75, 1500.75),
        (None, None),
        ("", None),
        ("уточняйте", None),
    ],
)
def test_parse_price_variants(raw: object, expected: float | None) -> None:
    assert parse_price(raw) == expected


def test_normalize_basic_row() -> None:
    mapping = ColumnMapping(article="Артикул", name="Название", price="Цена")
    row = {"Артикул": "A-1", "Название": "Гайка", "Цена": "12,50"}

    item, warning = normalize_row(row, mapping, source_file="t.xlsx", row_index=0)

    assert warning is None
    assert item is not None
    assert item.article == "A-1"
    assert item.price_rub == 12.5
    assert item.currency == "RUB"


def test_normalize_detects_usd_currency() -> None:
    mapping = ColumnMapping(article="SKU", name="Title", price="Price")
    row = {"SKU": "X-1", "Title": "Thing", "Price": "$50.00"}

    item, _ = normalize_row(row, mapping, source_file="t.csv", row_index=0)

    assert item is not None
    assert item.currency == "USD"
    assert item.price_rub == 50.0


def test_normalize_detects_eur_from_dedicated_column() -> None:
    mapping = ColumnMapping(
        article="Артикул",
        name="Название",
        price="Цена",
        currency="Валюта",
    )
    row = {"Артикул": "E-1", "Название": "Лампа", "Цена": "100", "Валюта": "EUR"}

    item, _ = normalize_row(row, mapping, source_file="t.csv", row_index=0)

    assert item is not None
    assert item.currency == "EUR"


def test_normalize_in_stock_yes_no() -> None:
    mapping = ColumnMapping(
        article="A",
        name="N",
        price="P",
        in_stock="S",
    )

    item_yes, _ = normalize_row(
        {"A": "1", "N": "Что-то", "P": "100", "S": "да"},
        mapping,
        source_file="t.csv",
        row_index=0,
    )
    item_no, _ = normalize_row(
        {"A": "2", "N": "Другое", "P": "100", "S": "нет"},
        mapping,
        source_file="t.csv",
        row_index=1,
    )
    item_count, _ = normalize_row(
        {"A": "3", "N": "Третье", "P": "100", "S": "15"},
        mapping,
        source_file="t.csv",
        row_index=2,
    )

    assert item_yes is not None and item_yes.in_stock is True
    assert item_no is not None and item_no.in_stock is False
    assert item_count is not None and item_count.in_stock is True


def test_empty_article_returns_warning() -> None:
    mapping = ColumnMapping(article="A", name="N", price="P")
    row = {"A": "", "N": "Что-то", "P": "100"}

    item, warning = normalize_row(row, mapping, source_file="t.csv", row_index=5)

    assert item is None
    assert warning is not None
    assert "5" in warning


def test_bad_price_keeps_item_with_warning() -> None:
    """Кривая цена не должна выкидывать всю позицию — только пометить warning'ом."""
    mapping = ColumnMapping(article="A", name="N", price="P")
    row = {"A": "X-1", "N": "Товар", "P": "по запросу"}

    item, warning = normalize_row(row, mapping, source_file="t.csv", row_index=2)

    assert item is not None
    assert item.price_rub is None
    assert warning is not None


def test_article_as_float_becomes_int_string() -> None:
    """Excel хранит «12345» как 12345.0 — мы должны вернуть строку без .0."""
    mapping = ColumnMapping(article="A", name="N", price="P")
    row = {"A": 12345.0, "N": "Что-то", "P": 99}

    item, _ = normalize_row(row, mapping, source_file="t.xlsx", row_index=0)

    assert item is not None
    assert item.article == "12345"
