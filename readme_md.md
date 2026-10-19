# streamstats

## Описание

Программа представляет собой потоковый анализатор лог-файлов.

Утилита обрабатывает файлы в форматах **JSONL** и **CSV**, накапливает статистику в реальном времени, корректно обрабатывает ошибки и выводит итоговый отчёт в формате JSON.

## Структура программы

```text
streamstats/
```

В этой папке находится весь код программы.

```text
tests/
```

В этой папке находятся тесты программы.

## Установка

Для работы программы необходимы Python и библиотека `pytest`.

Установить пакет и зависимости можно командой:

```powershell
python -m pip install -e .
```

Установить только `pytest` для тестов:

```powershell
python -m pip install pytest
```

## Запуск программы

Сначала откройте терминал в папке программы:

```powershell
cd "...\py-lab2"
```

После этого утилиту можно запускать через консольную команду.

## Использование (CLI)

Вывод отчёта по логам в консоль (stdout):

```powershell
python -m streamstats path/to/logs.jsonl
```

Сохранение отчёта в файл отчёта (`-o` / `--output`):

```powershell
python -m streamstats log1.jsonl log2.csv -o report.json
```

Пропуск битых строк вместо остановки с ошибкой (`--skip-invalid`):

```powershell
python -m streamstats logs.jsonl --skip-invalid
```

Принудительное указание формата (`--format`):

```powershell
python -m streamstats custom_log.txt --format jsonl
```

## Поддерживаемые возможности

```text
- Парсинг JSONL и CSV потоков
- Накопление статистики (total_events, skipped_events)
- Подсчет уровней логов (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Топ-5 источников ошибок (top_5_error_sources)
- Временной диапазон (time_range)
- Поддержка Unicode (кириллица, эмодзи)
```

## Тесты

Запустить все тесты:

```powershell
python -m pytest -v
```

Запустить конкретный файл с тестами:

```powershell
python -m pytest tests/all_tests.py -v
```

## Справка

Для просмотра справки программы выполните команду:

```powershell
python -m streamstats --help