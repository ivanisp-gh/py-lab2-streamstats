import argparse
import sys
from pathlib import Path

from streamstats.analysis import StatsAccumulator
from streamstats.errors import StreamStatsError, UnsupportedFormatError
from streamstats.parsers import parse_csv, parse_jsonl
from streamstats.report import format_json_report


def detect_format(file_path: Path, forced_format: str | None) -> str:
    """Определяет формат: по CLI флагу или по расширению файла."""
    if forced_format:
        return forced_format.lower()

    ext = file_path.suffix.lower()
    if ext == ".jsonl":
        return "jsonl"
    if ext == ".csv":
        return "csv"

    raise UnsupportedFormatError(
        f"Не удалось определить формат файла '{file_path}'. "
    )


def process_file(file_path: Path, file_format: str, skip_invalid: bool, stats: StatsAccumulator) -> None:
    """Читает файл потоком и передает в StatsAccumulator."""
    with open(file_path, "r", encoding="utf-8") as stream:
        if file_format == "csv":
            event_stream = parse_csv(stream)
        else:
            event_stream = parse_jsonl(stream)

        while True:
            try:
                line_no, event = next(event_stream)
                stats.add_event(event)
            except StopIteration:
                break
            except StreamStatsError as err:
                if skip_invalid:
                    stats.add_skipped()
                else:
                    print(
                        f"Ошибка в файле '{file_path}': {err}",
                        file=sys.stderr,
                    )
                    sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CLI-утилита для потокового анализа лог-файлов."
    )
    parser.add_argument(
        "files",
        nargs="+",
        type=Path,
        help="Пути к одному или нескольким файлам логов",
    )
    parser.add_argument(
        "--format",
        choices=["jsonl", "csv"],
        default=None,
        help="Принудительный формат логов (jsonl/csv)",
    )
    parser.add_argument(
        "--skip-invalid",
        action="store_true",
        help="Пропускать невалидные строки вместо остановки с ошибкой",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=None,
        help="Путь для сохранения итогового JSON (по умолчанию вывод в stdout)",
    )

    args = parser.parse_args()
    stats = StatsAccumulator()

    for file_path in args.files:
        if not file_path.is_file():
            print(f"Файл не найден: {file_path}", file=sys.stderr)
            sys.exit(1)

        try:
            fmt = detect_format(file_path, args.format)
            process_file(file_path, fmt, args.skip_invalid, stats)
        except UnsupportedFormatError as err:
            print(f"Ошибка: {err}", file=sys.stderr)
            sys.exit(1)

    result_json = format_json_report(stats.to_dict())

    if args.output:
        args.output.write_text(result_json, encoding="utf-8")
    else:
        print(result_json)


if __name__ == "__main__":
    main()
