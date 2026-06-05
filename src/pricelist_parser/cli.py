"""CLI и оркестрация пайплайна.

Пайплайн: extract → map (heuristic или LLM) → normalize → emit. Все шаги
вынесены в отдельные модули, здесь только склейка и разбор аргументов.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from pricelist_parser.extractors import extract
from pricelist_parser.formatters import emit_csv, emit_json
from pricelist_parser.mapping import map_columns_heuristic, map_columns_llm
from pricelist_parser.normalize import normalize_row
from pricelist_parser.schema import ColumnMapping, ParseResult


def parse_pricelist(
    input_path: Path,
    *,
    use_llm: bool = False,
) -> ParseResult:
    """Полный прогон пайплайна — функция, отдельная от CLI.

    Вызывается тестами и потенциально внешними скриптами. Возвращает
    готовый `ParseResult`, ничего не пишет в файлы — это делает CLI.
    """
    rows = extract(input_path)
    rows_total = len(rows)
    if not rows:
        return ParseResult(
            items=[],
            warnings=["Файл не содержит ни одной строки данных."],
            source_file=input_path.name,
            rows_total=0,
            rows_kept=0,
        )

    headers = list(rows[0].keys())

    mapping = _resolve_mapping(headers, use_llm=use_llm)
    if mapping.article is None or mapping.name is None:
        return ParseResult(
            items=[],
            warnings=[
                "Не удалось определить колонки артикула и/или названия. "
                "Попробуйте режим --llm или переименуйте заголовки.",
            ],
            source_file=input_path.name,
            rows_total=rows_total,
            rows_kept=0,
        )

    items = []
    warnings: list[str] = []
    for index, row in enumerate(rows):
        item, warning = normalize_row(
            row,
            mapping,
            source_file=input_path.name,
            row_index=index,
        )
        if item is not None:
            items.append(item)
        if warning:
            warnings.append(warning)

    return ParseResult(
        items=items,
        warnings=warnings,
        source_file=input_path.name,
        rows_total=rows_total,
        rows_kept=len(items),
    )


def _resolve_mapping(headers: list[str], *, use_llm: bool) -> ColumnMapping:
    """Сначала эвристика, потом LLM (если включена и эвристика промахнулась).

    Эвристика дешёвая и моментальная — нет смысла гонять LLM, если
    обычные «Артикул»/«Наименование»/«Цена» уже нашлись. LLM врубаем
    только когда базовый mapping неполный.
    """
    base = map_columns_heuristic(headers)
    if not use_llm:
        return base
    if base.article and base.name and base.price:
        return base

    try:
        return map_columns_llm(headers)
    except Exception:
        # При любой ошибке LLM откатываемся на эвристику — пользователь
        # получит partial-результат, а не падение.
        return base


def main(argv: list[str] | None = None) -> int:
    """Точка входа CLI. Возвращает exit-code (0 — успех)."""
    parser = argparse.ArgumentParser(
        prog="pricelist-parser",
        description="Парсит прайс-листы (.xlsx/.csv/.html/.json) в единую схему.",
    )
    parser.add_argument("input", type=Path, help="Путь к исходному файлу.")
    parser.add_argument(
        "--out",
        type=Path,
        required=True,
        help="Куда писать результат. Расширение определяет формат (.json или .csv).",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Дёрнуть локальную Ollama для разметки нестандартных колонок.",
    )

    args = parser.parse_args(argv)

    if not args.input.exists():
        print(f"Файл не найден: {args.input}", file=sys.stderr)
        return 2

    result = parse_pricelist(args.input, use_llm=args.llm)

    suffix = args.out.suffix.lower()
    if suffix == ".csv":
        emit_csv(result, args.out)
    elif suffix == ".json":
        emit_json(result, args.out)
    else:
        print(
            f"Неизвестное расширение для --out: {suffix!r}. Используйте .json или .csv.",
            file=sys.stderr,
        )
        return 2

    print(
        f"Готово: {result.rows_kept}/{result.rows_total} строк сохранено в {args.out}",
        file=sys.stderr,
    )
    if result.warnings:
        print(f"Предупреждений: {len(result.warnings)}", file=sys.stderr)
    return 0


def run() -> None:
    """Alias для тестов и embed-сценариев."""
    raise SystemExit(main())
