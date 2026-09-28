"""Тесты эвристического mapping заголовков.

Проверяем разные варианты «как клиент назвал колонку», включая
русско-английскую смесь и косвенные синонимы.
"""

from __future__ import annotations

from pricelist_parser.mapping.heuristic import map_columns_heuristic


def test_standard_russian_headers() -> None:
    mapping = map_columns_heuristic(["Артикул", "Наименование", "Цена, руб", "В наличии"])

    assert mapping.article == "Артикул"
    assert mapping.name == "Наименование"
    assert mapping.price == "Цена, руб"
    assert mapping.in_stock == "В наличии"


def test_sku_instead_of_article() -> None:
    mapping = map_columns_heuristic(["SKU", "Товар", "Стоимость"])

    assert mapping.article == "SKU"
    assert mapping.name == "Товар"
    assert mapping.price == "Стоимость"


def test_code_instead_of_article() -> None:
    mapping = map_columns_heuristic(["Код товара", "Название", "Цена"])

    assert mapping.article == "Код товара"
    assert mapping.name == "Название"


def test_english_headers() -> None:
    mapping = map_columns_heuristic(["Vendor Code", "Product Name", "Price", "Stock"])

    assert mapping.article == "Vendor Code"
    assert mapping.name == "Product Name"
    assert mapping.price == "Price"
    assert mapping.in_stock == "Stock"


def test_missing_optional_fields() -> None:
    """Если в исходнике нет валюты/остатка — это не ошибка."""
    mapping = map_columns_heuristic(["Артикул", "Наименование", "Цена"])

    assert mapping.currency is None
    assert mapping.in_stock is None


def test_no_double_assignment_of_same_header() -> None:
    """«Цена руб» не должна одновременно стать price и currency."""
    mapping = map_columns_heuristic(["Артикул", "Название", "Цена руб"])

    assert mapping.price == "Цена руб"
    assert mapping.currency is None


def test_retail_price_header_from_1c_export() -> None:
    """Выгрузка из 1С: цена называется «Розница», слова «цена» в шапке нет."""
    mapping = map_columns_heuristic(["Код 1С", "Номенклатура", "Розница за упак.", "Наличие"])

    assert mapping.price == "Розница за упак."
