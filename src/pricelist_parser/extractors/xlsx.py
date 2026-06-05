"""Извлечение строк из .xlsx через openpyxl.

Берём первый лист и считаем, что первая непустая строка — это заголовки.
В реальных прайсах бывают «шапки» с логотипом и пустые строки сверху,
поэтому мы пропускаем ведущие пустые строки до первой содержательной.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from openpyxl import load_workbook


def extract_xlsx(path: Path) -> list[dict[str, Any]]:
    """Возвращает список словарей {заголовок: значение} по первому листу.

    `data_only=True` — берём вычисленные значения формул, а не сами формулы.
    Без этого в строковом представлении можно получить `=SUM(...)` вместо числа.
    """
    workbook = load_workbook(filename=str(path), read_only=True, data_only=True)
    try:
        worksheet = workbook.active
        if worksheet is None:
            return []

        rows_iter = worksheet.iter_rows(values_only=True)
        headers: list[str] = []
        for row in rows_iter:
            if not row:
                continue
            non_empty = [cell for cell in row if cell not in (None, "")]
            # Логотипы и одностолбцовые подписи («Прайс компании Х») имеют
            # одну непустую ячейку — пропускаем их и продолжаем искать
            # настоящую шапку. Реальные заголовки прайса — два и больше.
            if len(non_empty) < 2:
                continue
            headers = [str(cell).strip() if cell is not None else "" for cell in row]
            while headers and headers[-1] == "":
                headers.pop()
            break

        if not headers:
            return []

        out: list[dict[str, Any]] = []
        for row in rows_iter:
            if not row or all(cell in (None, "") for cell in row):
                # Пустые строки между блоками — пропускаем, а не обрываем.
                continue
            record: dict[str, Any] = {}
            for index, header in enumerate(headers):
                value = row[index] if index < len(row) else None
                record[header] = value
            out.append(record)
        return out
    finally:
        workbook.close()
