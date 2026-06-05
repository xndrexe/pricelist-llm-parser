"""Извлечение первой таблицы из .html через BeautifulSoup.

Берём именно первую таблицу, потому что в верстке прайс-листов вторые-третьи
таблицы — это обычно сноски и «реквизиты», а не товары. Если первая таблица
не та — это редкий случай, и пользователю проще руками отрезать лишнее,
чем выкручиваться с эвристиками «какая таблица настоящая».
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup, Tag


def extract_html(path: Path) -> list[dict[str, Any]]:
    """Возвращает строки первой `<table>` в HTML-файле.

    Заголовки берём в порядке: явные `<th>` → если нет, первая строка `<tr>`.
    """
    html = path.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table")
    if not isinstance(table, Tag):
        return []

    rows = table.find_all("tr")
    if not rows:
        return []

    # Шапка: ищем <th> в первой строке. Если их нет — первая строка считается
    # заголовочной, и в данных она уже не учитывается.
    first_row = rows[0]
    header_cells = first_row.find_all("th") if isinstance(first_row, Tag) else []
    if header_cells:
        headers = [cell.get_text(strip=True) for cell in header_cells]
        data_rows = rows[1:]
    else:
        first_cells = first_row.find_all(["td", "th"]) if isinstance(first_row, Tag) else []
        headers = [cell.get_text(strip=True) for cell in first_cells]
        data_rows = rows[1:]

    out: list[dict[str, Any]] = []
    for row in data_rows:
        if not isinstance(row, Tag):
            continue
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        record: dict[str, Any] = {}
        for index, header in enumerate(headers):
            record[header] = cells[index].get_text(strip=True) if index < len(cells) else None
        out.append(record)
    return out
