"""Тесты извлекателя HTML-таблиц."""

from __future__ import annotations

from pathlib import Path

from pricelist_parser.extractors.html import extract_html


def test_extracts_first_table_only(html_table: Path) -> None:
    rows = extract_html(html_table)

    # В фикстуре две таблицы — должна попасть только первая (с товарами).
    assert len(rows) == 2
    assert rows[0]["Артикул"] == "H-1"
    assert rows[0]["Цена руб"] == "120"


def test_html_without_tables_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "no_table.html"
    path.write_text("<html><body><p>Нет таблиц</p></body></html>", encoding="utf-8")

    rows = extract_html(path)

    assert rows == []


def test_html_table_without_th(tmp_path: Path) -> None:
    """Таблицы без `<th>` тоже встречаются — первая строка считается шапкой."""
    path = tmp_path / "no_th.html"
    path.write_text(
        """
        <html><body><table>
            <tr><td>Артикул</td><td>Название</td><td>Цена</td></tr>
            <tr><td>X-1</td><td>Что-то</td><td>100</td></tr>
        </table></body></html>
        """,
        encoding="utf-8",
    )

    rows = extract_html(path)

    assert len(rows) == 1
    assert rows[0]["Артикул"] == "X-1"
