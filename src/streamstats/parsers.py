import csv
import json
from datetime import datetime
from typing import Iterator, TextIO

from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.models import LogEvent

V_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def validate_and_create_event(data: dict) -> LogEvent:
    """Проверяет словарь с данными одной строки и собирает LogEvent."""
    required_fields = ("timestamp", "level", "source", "message")
    for field in required_fields:
        if field not in data:
            raise InvalidEventError(f"Отсутствует поле: {field}")

    raw_ts = data["timestamp"]
    if type(raw_ts) is not str:
        raise InvalidTimestampError("Поле timestamp должно быть строкой")
    try:
        ts = datetime.fromisoformat(raw_ts)
    except (ValueError, TypeError) as exc:
        raise InvalidTimestampError(f"Неверный формат даты: {raw_ts}") from exc

    level = data["level"]
    if type(level) is not str or level not in V_LEVELS:
        raise InvalidEventError(f"Недопустимый уровень: {level}")

    source = data["source"]
    if type(source) is not str or not source.strip(): #учитывается пустая строка
        raise InvalidEventError("Поле source не может быть пустым")

    message = data["message"]
    if type(message) is not str:
        raise InvalidEventError("Поле message должно быть строкой")

    return LogEvent(timestamp=ts, level=level, source=source.strip(), message=message)


def parse_jsonl(stream: TextIO, line_no: int = 0) -> Iterator[tuple[int, LogEvent]]:
    """Построчно читает поток JSONL + счётчик"""
    for raw_line in stream:
        line_no += 1
        line = raw_line.strip()
        if not line:
            continue

        try:
            raw_data = json.loads(line)
        except json.JSONDecodeError as exc:
            raise InvalidEventError(f"Сломанный JSON в строке {line_no}") from exc

        if type(raw_data) is not dict:
            raise InvalidEventError(f"Строка {line_no} не является JSON-объектом")

        event = validate_and_create_event(raw_data)
        yield line_no, event


def parse_csv(stream: TextIO, line_no: int = 0) -> Iterator[tuple[int, LogEvent]]:
    """Построчно читает поток CSV + счетчик"""
    reader = csv.DictReader(stream)
    if line_no == 0:
        line_no = 1

    for row in reader:
        line_no += 1
        event = validate_and_create_event(row)
        yield line_no, event