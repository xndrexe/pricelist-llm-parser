"""Сквозной тест: загрузить файл → пройти пайплайн → проверить JSON-вывод."""

from __future__ import annotations

import json
from pathlib import Path

from pricelist_parser.cli import parse_pricelist
from pricelist_parser.formatters import emit_json


def test_e2e_simple_xlsx_to_json(simple_xlsx: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "result.json"

    result = parse_pricelist(simple_xlsx)
    emit_json(result, out_path)

    raw = json.loads(out_path.read_text(encoding="utf-8"))
    assert raw["rows_total"] == 3
    assert raw["rows_kept"] == 3
    assert len(raw["items"]) == 3

    first = raw["items"][0]
    assert first["article"] == "A-001"
    assert first["name"] == "Гайка М6"
    assert first["price_rub"] == 12.5
    assert first["currency"] == "RUB"
    assert first["in_stock"] is True


def test_e2e_messy_xlsx_uses_real_headers(messy_xlsx: Path, tmp_path: Path) -> None:
    """Mess-фикстура имеет шапку с логотипом — пайплайн должен её пропустить."""
    result = parse_pricelist(messy_xlsx)

    assert result.rows_kept == 2
    assert result.items[0].article == "SKU-100"
    assert result.items[0].price_rub == 1250.50


def test_e2e_csv_to_json(csv_semicolon: Path, tmp_path: Path) -> None:
    out_path = tmp_path / "csv_result.json"

    result = parse_pricelist(csv_semicolon)
    emit_json(result, out_path)

    raw = json.loads(out_path.read_text(encoding="utf-8"))
    assert raw["rows_kept"] == 2
    assert raw["items"][0]["price_rub"] == 350.0


def test_e2e_html_to_json(html_table: Path) -> None:
    result = parse_pricelist(html_table)

    assert result.rows_kept == 2
    assert result.items[0].article == "H-1"
    assert result.items[0].price_rub == 120.0


def test_e2e_missing_price_column_is_reported(tmp_path: Path) -> None:
    """Колонку цены не нашли — позиции остаются, но об этом есть предупреждение."""
    path = tmp_path / "no_price.csv"
    path.write_text("Артикул;Наименование;Что-то\nA-1;Гайка;12\n", encoding="utf-8")

    result = parse_pricelist(path)

    assert result.rows_kept == 1
    assert result.items[0].price_rub is None
    assert any("цен" in warning.lower() for warning in result.warnings)
