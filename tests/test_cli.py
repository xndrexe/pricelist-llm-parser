"""Тесты CLI-обвязки: разбор аргументов, выбор формата вывода."""

from __future__ import annotations

import json
from pathlib import Path

from pricelist_parser.cli import main


def test_cli_writes_json_output(simple_xlsx: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.json"

    code = main([str(simple_xlsx), "--out", str(out)])

    assert code == 0
    raw = json.loads(out.read_text(encoding="utf-8"))
    assert raw["rows_kept"] == 3


def test_cli_writes_csv_output(simple_xlsx: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.csv"

    code = main([str(simple_xlsx), "--out", str(out)])

    assert code == 0
    content = out.read_text(encoding="utf-8-sig")
    assert "article" in content.splitlines()[0]
    assert "A-001" in content


def test_cli_unknown_format_returns_error(simple_xlsx: Path, tmp_path: Path) -> None:
    out = tmp_path / "out.xml"

    code = main([str(simple_xlsx), "--out", str(out)])

    assert code == 2


def test_cli_missing_input_returns_error(tmp_path: Path) -> None:
    out = tmp_path / "out.json"

    code = main([str(tmp_path / "does_not_exist.xlsx"), "--out", str(out)])

    assert code == 2
