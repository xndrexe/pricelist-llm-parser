"""Извлекатели «сырых» строк из файлов разных форматов.

Контракт всех извлекателей одинаков: на вход — путь к файлу,
на выход — `list[dict[str, Any]]`, где ключи — оригинальные заголовки
колонок, значения — содержимое ячеек как строки (или числа/None).

Намеренно НЕ пытаемся угадывать смысл колонок здесь — это работа
следующего слоя (`mapping/`). Извлекатель тупой и предсказуемый.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pricelist_parser.extractors.csv import extract_csv
from pricelist_parser.extractors.html import extract_html
from pricelist_parser.extractors.json_file import extract_json
from pricelist_parser.extractors.xlsx import extract_xlsx


def extract(path: Path) -> list[dict[str, Any]]:
    """Диспетчер по расширению. Бросает ValueError для незнакомых форматов.

    Намеренно идём по расширению, а не по сигнатуре файла — большинство
    клиентских прайсов приходят с честным расширением, а магия с magic-байтами
    добавляет ошибок там, где их не было.
    """
    suffix = path.suffix.lower()
    if suffix in {".xlsx", ".xlsm"}:
        return extract_xlsx(path)
    if suffix == ".csv":
        return extract_csv(path)
    if suffix in {".html", ".htm"}:
        return extract_html(path)
    if suffix == ".json":
        return extract_json(path)
    raise ValueError(f"Неподдерживаемое расширение: {suffix!r}")


__all__ = ["extract", "extract_csv", "extract_html", "extract_json", "extract_xlsx"]
