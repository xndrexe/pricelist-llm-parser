"""Тесты на автодетекцию разделителя CSV."""

from __future__ import annotations

from pathlib import Path

from pricelist_parser.extractors.csv import extract_csv


def test_csv_with_semicolon_separator(csv_semicolon: Path) -> None:
    rows = extract_csv(csv_semicolon)

    assert len(rows) == 2
    assert rows[0]["Артикул"] == "B-1"
    # BOM не должен попасть в имя ключа — проверяем именно «Артикул», а не «﻿Артикул».
    assert "﻿Артикул" not in rows[0]


def test_csv_with_comma_separator(csv_comma: Path) -> None:
    rows = extract_csv(csv_comma)

    assert len(rows) == 2
    assert rows[0]["Code"] == "C-1"
    assert rows[1]["Price"] == "15.75"


def test_csv_empty_file_returns_empty_list(tmp_path: Path) -> None:
    """Пустой CSV — это не ошибка, а просто 0 строк."""
    path = tmp_path / "empty.csv"
    path.write_text("Артикул;Наименование;Цена\n", encoding="utf-8")

    rows = extract_csv(path)

    assert rows == []
