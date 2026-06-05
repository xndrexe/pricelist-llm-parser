"""Тесты JSON-извлекателя."""

from __future__ import annotations

from pathlib import Path

import pytest

from pricelist_parser.extractors.json_file import extract_json


def test_top_level_array(json_array: Path) -> None:
    rows = extract_json(json_array)

    assert len(rows) == 2
    assert rows[0]["article"] == "J-1"


def test_wrapped_with_items_key(json_wrapped: Path) -> None:
    rows = extract_json(json_wrapped)

    assert len(rows) == 1
    assert rows[0]["Артикул"] == "W-1"


def test_invalid_structure_raises(tmp_path: Path) -> None:
    """JSON без ожидаемой структуры должен явно падать, а не возвращать []."""
    path = tmp_path / "bad.json"
    path.write_text('{"foo": "bar"}', encoding="utf-8")

    with pytest.raises(ValueError):
        extract_json(path)
