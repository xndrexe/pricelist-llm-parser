# pricelist-llm-parser

[![CI](https://github.com/xndrexe/pricelist-llm-parser/actions/workflows/ci.yml/badge.svg)](https://github.com/xndrexe/pricelist-llm-parser/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

CLI-утилита, которая берёт прайс-лист в любом из четырёх форматов
(.xlsx / .csv / .html / .json) и приводит его к единой Pydantic-схеме.
Колонки определяет либо словарём синонимов, либо локальной LLM через
Ollama — на ваш выбор. Никаких облачных API, никаких C++-зависимостей,
никаких бинарников в репо — все фикстуры генерируются программно.

## Зачем это

У клиентов прайс-листы выглядят как «Артикул / Наименование / Цена руб»,
«SKU / Title / Price USD», «Код 1С / Номенклатура / Розница за упак.» —
и всё это надо привести к единой схеме чтобы дальше работать с
позициями. Эта утилита автоматизирует приведение, не задаёт лишних
вопросов и не требует подгонять данные руками.

## Поддерживаемые форматы

| Расширение      | Извлекатель                          | Что внутри    |
|-----------------|--------------------------------------|---------------|
| `.xlsx` `.xlsm` | `openpyxl` (read-only, data-only)    | Первый лист, шапка определяется по первой непустой строке |
| `.csv`          | стандартный `csv` + `csv.Sniffer`    | Автодетекция разделителя (`,` / `;` / `\t` / `|`), BOM режется |
| `.html` `.htm`  | `BeautifulSoup` + `lxml`             | Первая `<table>` на странице |
| `.json`         | стандартный `json`                   | Массив объектов на верхнем уровне или `{items|data|rows|products: [...]}` |

## Установка

```bash
python -m venv .venv
.venv/Scripts/activate   # Windows
# source .venv/bin/activate   # Linux/Mac
pip install -e ".[dev]"
```

## Использование

### Базовый режим — эвристика

```bash
python -m pricelist_parser examples/sample.xlsx --out result.json
python -m pricelist_parser examples/sample.csv  --out result.csv
```

Утилита сама определит формат входа по расширению и формат выхода
по расширению `--out`. Поддерживаются `.json` и `.csv` на выход.

### Режим с LLM — для нестандартных заголовков

```bash
# Заранее: ollama pull qwen2.5:7b-instruct
python -m pricelist_parser difficult.xlsx --out result.json --llm
```

В режиме `--llm` парсер сначала прогоняет заголовки через эвристику.
Если она нашла все ключевые колонки (`article`, `name`, `price`) — LLM не
дёргаем, ускоряемся. Если что-то осталось пустым — отправляем заголовки
в локальную Ollama. Сеть наружу не уходит, всё крутится в localhost.

## Формат вывода

```jsonc
{
  "items": [
    {
      "article": "A-001",
      "name": "Гайка М6",
      "price_rub": 12.5,
      "currency": "RUB",
      "in_stock": true,
      "source_file": "sample.xlsx",
      "row_index": 0
    }
  ],
  "warnings": [
    "Артикул B-114: не удалось разобрать цену 'по запросу'."
  ],
  "source_file": "sample.xlsx",
  "rows_total": 25,
  "rows_kept": 24
}
```

CSV-вывод содержит только `items` без warning'ов — открывается напрямую
в Excel/LibreOffice без шума.

## Что осознанно НЕ сделано

- **Без авто-конвертации валют.** Если в исходнике долларовая цена —
  поле `currency` будет `USD`, но `price_rub` останется как есть. К ЦБ за
  курсом не ходим: курс — это бизнес-решение клиента (закупочный, продажный,
  с маржой), а не задача парсера.
- **Без выбора листа в xlsx.** Берём активный (первый) лист. Прайсы с
  несколькими листами — отдельная история, требует UI-выбора.
- **Без поддержки .xls (Office 97-2003).** Только .xlsx. xlrd для старого
  формата тащит лишние зависимости, выпало из современных версий и
  больше не поддерживается.
- **Без батч-режима по папке.** CLI принимает один файл. Для пачки —
  shell-цикл (`for f in *.xlsx; do ...`). Это меньше скрытых поведений
  «один сломался, остальные пропустить или нет».
- **Без retry на Ollama.** Один запрос — если упал, откатываемся на
  эвристику. Локальная Ollama либо отвечает быстро, либо что-то совсем
  не так — повторные попытки только маскируют проблему.
- **Без авто-маппинга для unicode-числовых форматов.** Поддерживаем три
  основных формата чисел (русский с пробелами, английский с запятой,
  простой с точкой). Экзотика типа индийских «лакхов» не входит.
- **Без CLI-флага «верни не-валидные позиции отдельно».** Сейчас они
  идут в `warnings`, без отдельного файла. Если потребуется — добавим.

## Стек

- Python 3.11+
- pydantic + pydantic-settings (схемы, конфиг через `PRICELIST_*`)
- openpyxl (xlsx)
- beautifulsoup4 + lxml (html)
- httpx (Ollama-клиент)
- pytest, ruff, mypy (dev)

Все зависимости — чисто Python, **никаких** chromadb/faiss/hnswlib и
прочих библиотек, требующих C++-компилятора. Ставится одной командой
на любом Windows без Visual Studio Build Tools.

## Тесты

```bash
pytest -q
```

Покрывают: все четыре извлекателя (включая mess-варианты с шапками и
HTML без `<th>`), эвристический mapping на 6 разных вариантах
заголовков, нормализацию чисел (12 форматов цены и наличия), сквозной
прогон xlsx → JSON, CLI-обвязку (4 кейса), LLM-mapping с моком httpx
(4 сценария включая «модель выдумала колонку»).

LLM-интеграция тестируется без реальной Ollama — через `httpx.MockTransport`
с детерминированными ответами. Никаких сетевых вызовов в тестах.

## Архитектура

См. [docs/architecture.md](docs/architecture.md).

## Docker

```bash
docker build -t pricelist-parser .
docker run --rm -v "$PWD":/work pricelist-parser /work/sample.xlsx --out /work/result.json
```

## Лицензия

MIT.

## Контекст

Это публичная демонстрация моего стека для ETL/парсинга разнородных
данных. Боевые системы (8+ месяцев в проде, многоканальная агрегация
из десятков источников с расхождениями и сверками) идут под NDA —
архитектуру разберу на созвоне по запросу.

Контакт: [skostuhov@gmail.com](mailto:skostuhov@gmail.com) /
[GitHub @xndrexe](https://github.com/xndrexe).
