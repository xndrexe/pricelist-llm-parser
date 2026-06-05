"""Слой определения соответствия «заголовок исходника → поле схемы».

Эвристика быстрая и без сети. LLM-вариант — для прайсов с креативными
названиями колонок («Цена с НДС за коробку», «Код 1С», «Шт. на руках»).
"""

from __future__ import annotations

from pricelist_parser.mapping.heuristic import map_columns_heuristic
from pricelist_parser.mapping.llm import map_columns_llm

__all__ = ["map_columns_heuristic", "map_columns_llm"]
