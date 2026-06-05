"""Запуск пакета как модуля: `python -m pricelist_parser ...`.

Тонкая обёртка — вся логика разбора аргументов и пайплайн в `cli`.
"""

from __future__ import annotations

from pricelist_parser.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
