"""Извлечение строк из .csv с детекцией разделителя.

CSV в дикой природе пишут через `,`, `;` и `\\t`, причём `;` встречается
особенно часто в русских выгрузках, где запятая занята дробным
разделителем в числах. `csv.Sniffer` сам решает по первой пачке байт.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any


def extract_csv(path: Path) -> list[dict[str, Any]]:
    """Читает CSV-файл с автодетекцией разделителя и BOM.

    `utf-8-sig` сам сжирает BOM, если он есть — иначе первый заголовок
    оказался бы «\\ufeffАртикул» и mapping не сработал бы.
    """
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        sample = fh.read(8192)
        fh.seek(0)
        delimiter = _detect_delimiter(sample)
        reader = csv.DictReader(fh, delimiter=delimiter)
        return [dict(row) for row in reader]


def _detect_delimiter(sample: str) -> str:
    """Подбирает разделитель по первой непустой строке.

    Sniffer csv-модуля часто промахивается на русских прайсах, потому что
    значения цен содержат запятую («12,50») и Sniffer выбирает её как
    разделитель полей. Поэтому используем простую эвристику: смотрим
    на заголовок и выбираем разделитель, который делит его на максимум
    колонок (>=2). При равенстве — приоритет `;` (типично для 1С-выгрузок).
    """
    first_line = next((line for line in sample.splitlines() if line.strip()), "")
    if not first_line:
        return ";"

    candidates = [";", "\t", "|", ","]
    best = ";"
    best_count = 1
    for delim in candidates:
        count = first_line.count(delim)
        if count > best_count:
            best_count = count
            best = delim
    return best
