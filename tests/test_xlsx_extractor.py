"""Тесты извлекателя xlsx."""

from __future__ import annotations

from pathlib import Path

from pricelist_parser.extractors.xlsx import extract_xlsx


def test_simple_xlsx_returns_rows_with_headers(simple_xlsx: Path) -> None:
    rows = extract_xlsx(simple_xlsx)

    assert len(rows) == 3
    assert set(rows[0].keys()) == {"Артикул", "Наименование", "Цена, руб", "В наличии"}
    assert rows[0]["Артикул"] == "A-001"
    assert rows[0]["Цена, руб"] == 12.50


def test_messy_xlsx_skips_leading_empty_rows(messy_xlsx: Path) -> None:
    """Шапка с логотипом и пустые строки сверху не должны ломать парсинг."""
    rows = extract_xlsx(messy_xlsx)

    assert len(rows) == 2
    assert rows[0]["SKU"] == "SKU-100"
    assert rows[1]["Остаток"] == 0
