"""Общие фикстуры тестов.

Все «реальные» прайсы генерируются программно — это позволяет хранить
фикстуры в git без бинарных файлов и легко добавлять новые варианты,
не открывая Excel руками.
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from openpyxl import Workbook


@pytest.fixture(scope="session")
def fixtures_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Каталог временных фикстур на всю сессию.

    Кладём всё в tmp, потому что нам не нужны бинарники в репозитории.
    Прайсы генерируются один раз на запуск, используются всеми тестами.
    """
    return tmp_path_factory.mktemp("fixtures")


@pytest.fixture(scope="session")
def simple_xlsx(fixtures_dir: Path) -> Path:
    """Простой xlsx с русскими заголовками — happy-path."""
    path = fixtures_dir / "simple.xlsx"
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["Артикул", "Наименование", "Цена, руб", "В наличии"])
    ws.append(["A-001", "Гайка М6", 12.50, "да"])
    ws.append(["A-002", "Болт М8x40", 18.00, "нет"])
    ws.append(["A-003", "Шайба", 1.20, 15])
    wb.save(path)
    return path


@pytest.fixture(scope="session")
def messy_xlsx(fixtures_dir: Path) -> Path:
    """Xlsx с шапкой/пустыми строками сверху и нестандартными колонками."""
    path = fixtures_dir / "messy.xlsx"
    wb = Workbook()
    ws = wb.active
    assert ws is not None
    ws.append(["Прайс компании Альфа", None, None, None])
    ws.append([None, None, None, None])
    ws.append(["SKU", "Товар", "Стоимость", "Остаток"])
    ws.append(["SKU-100", "Подшипник 6202", "1 250,50", 7])
    ws.append(["SKU-101", "Сальник", "350.00", 0])
    wb.save(path)
    return path


@pytest.fixture(scope="session")
def csv_semicolon(fixtures_dir: Path) -> Path:
    """CSV с разделителем `;` — типичный экспорт из 1С."""
    path = fixtures_dir / "semicolon.csv"
    with path.open("w", encoding="utf-8-sig", newline="") as fh:
        writer = csv.writer(fh, delimiter=";")
        writer.writerow(["Артикул", "Наименование", "Цена"])
        writer.writerow(["B-1", "Ключ рожковый 10", "350,00"])
        writer.writerow(["B-2", "Ключ накидной 13", "420,00"])
    return path


@pytest.fixture(scope="session")
def csv_comma(fixtures_dir: Path) -> Path:
    """CSV с запятой как разделителем и точкой в числах."""
    path = fixtures_dir / "comma.csv"
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter=",")
        writer.writerow(["Code", "Title", "Price"])
        writer.writerow(["C-1", "Hammer", "12.50"])
        writer.writerow(["C-2", "Wrench", "15.75"])
    return path


@pytest.fixture(scope="session")
def html_table(fixtures_dir: Path) -> Path:
    """HTML-страница с одной таблицей внутри обёртки.

    Часть прайсов клиенты выгружают «сохранить как .html» из Excel —
    важно проверить, что мы достанем именно первую `<table>`.
    """
    path = fixtures_dir / "table.html"
    path.write_text(
        """
        <html><body>
        <h1>Прайс</h1>
        <table>
            <tr><th>Артикул</th><th>Название</th><th>Цена руб</th></tr>
            <tr><td>H-1</td><td>Лампочка E27 9Вт</td><td>120</td></tr>
            <tr><td>H-2</td><td>Лампочка E14 7Вт</td><td>95</td></tr>
        </table>
        <table>
            <tr><th>Реквизиты</th></tr>
            <tr><td>ООО Ромашка</td></tr>
        </table>
        </body></html>
        """,
        encoding="utf-8",
    )
    return path


@pytest.fixture(scope="session")
def json_array(fixtures_dir: Path) -> Path:
    """JSON-массив объектов — наиболее частый случай прямых выгрузок."""
    path = fixtures_dir / "array.json"
    data: list[dict[str, Any]] = [
        {"article": "J-1", "name": "Кабель USB-C 1м", "price": 450, "currency": "RUB"},
        {"article": "J-2", "name": "Кабель USB-C 2м", "price": 590, "currency": "RUB"},
    ]
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture(scope="session")
def json_wrapped(fixtures_dir: Path) -> Path:
    """JSON с обёрткой `{items: [...]}` — тоже встречается."""
    path = fixtures_dir / "wrapped.json"
    data = {
        "exported_at": "2026-01-01",
        "items": [
            {"Артикул": "W-1", "Наименование": "Зарядное 20Вт", "Цена": 1200},
        ],
    }
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return path


@pytest.fixture
def parsed_pipeline_result() -> Iterator[None]:
    """Заглушка-пример для будущих расширений. Сейчас просто yield."""
    yield None
