import io
import json
import sys
import pytest

from streamstats.parsers import parse_jsonl, parse_csv
from streamstats.analysis import StatsAccumulator
from streamstats.report import format_json_report
from streamstats.errors import InvalidEventError, InvalidTimestampError
from streamstats.__main__ import process_file, main


# 1. Unit tests обоих parsers
def test_parse_jsonl():
    text = '{"timestamp": "2026-01-01T10:00:00", "level": "INFO", "source": "auth", "message": "login"}\n'
    res = list(parse_jsonl(io.StringIO(text)))

    assert res[0][0] == 1
    assert res[0][1].level == "INFO"
    assert res[0][1].source == "auth"
    assert res[0][1].message == "login"


def test_parse_csv():
    text = "timestamp,level,source,message\n2026-01-01T11:00:00,ERROR,db,timeout\n"
    res = list(parse_csv(io.StringIO(text)))

    assert res[0][0] == 2
    assert res[0][1].level == "ERROR"
    assert res[0][1].source == "db"
    assert res[0][1].message == "timeout"


# 2. Тест пустого файла
def test_empty_jsonl():
    assert list(parse_jsonl(io.StringIO(""))) == []
    assert list(parse_jsonl(io.StringIO("   \n\n"))) == []


def test_empty_csv():
    assert list(parse_csv(io.StringIO(""))) == []
    assert list(parse_csv(io.StringIO("timestamp,level,source,message\n"))) == []


# 3. Тест повреждённой строки в обоих режимах
def test_corrupted_line_strict_mode(tmp_path):
    with pytest.raises(InvalidEventError):
        list(parse_jsonl(io.StringIO("broken_json\n")))

    with pytest.raises(InvalidTimestampError):
        list(parse_csv(io.StringIO("timestamp,level,source,message\nbad_date,INFO,db,ok\n")))

    file = tmp_path / "broken.jsonl"
    file.write_text("broken_json\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        process_file(file, "jsonl", False, StatsAccumulator())


def test_corrupted_line_skip_mode(tmp_path):
    file = tmp_path / "broken.jsonl"
    file.write_text(
        '{"timestamp": "2026-01-01T10:00:00", "level": "INFO", "source": "app", "message": "ok"}\n'
        'broken_json\n',
        encoding="utf-8",
    )

    stats = StatsAccumulator()
    process_file(file, "jsonl", True, stats)

    assert stats.total_events == 1
    assert stats.skipped_events == 1


# 4. Тест нескольких файлов
def test_multiple_files_counts(tmp_path):
    f1 = tmp_path / "1.jsonl"
    f2 = tmp_path / "2.csv"

    f1.write_text('{"timestamp": "2026-01-01T10:00:00", "level": "INFO", "source": "s1", "message": "m1"}\n', encoding="utf-8")
    f2.write_text("timestamp,level,source,message\n2026-01-01T12:00:00,ERROR,s2,m2\n", encoding="utf-8")

    stats = StatsAccumulator()
    process_file(f1, "jsonl", False, stats)
    process_file(f2, "csv", False, stats)

    assert stats.total_events == 2
    assert stats.level_counts["INFO"] == 1
    assert stats.level_counts["ERROR"] == 1


def test_multiple_files_time_and_errors(tmp_path):
    f1 = tmp_path / "1.jsonl"
    f2 = tmp_path / "2.jsonl"

    f1.write_text('{"timestamp": "2026-01-01T15:00:00", "level": "ERROR", "source": "db", "message": "e1"}\n', encoding="utf-8")
    f2.write_text('{"timestamp": "2026-01-01T09:00:00", "level": "CRITICAL", "source": "db", "message": "e2"}\n', encoding="utf-8")

    stats = StatsAccumulator()
    process_file(f1, "jsonl", False, stats)
    process_file(f2, "jsonl", False, stats)

    data = stats.to_dict()
    assert data["time_range"]["first_event"] == "2026-01-01T09:00:00"
    assert data["time_range"]["last_event"] == "2026-01-01T15:00:00"
    assert data["top_5_error_sources"] == [{"source": "db", "count": 2}]


# 5. Тест Unicode
def test_unicode_parsers():
    jsonl = '{"timestamp": "2026-01-01T10:00:00", "level": "INFO", "source": "сервер", "message": "Привет 🔥"}\n'
    csv = "timestamp,level,source,message\n2026-01-01T10:00:00,ERROR,база,Ошибка 東京\n"

    res_jsonl = list(parse_jsonl(io.StringIO(jsonl)))
    res_csv = list(parse_csv(io.StringIO(csv)))

    assert res_jsonl[0][1].source == "сервер"
    assert res_jsonl[0][1].message == "Привет 🔥"
    assert res_csv[0][1].source == "база"
    assert res_csv[0][1].message == "Ошибка 東京"


def test_unicode_report():
    text = '{"timestamp": "2026-01-01T10:00:00", "level": "ERROR", "source": "ядро", "message": "Сбой"}\n'
    _, event = next(parse_jsonl(io.StringIO(text)))

    stats = StatsAccumulator()
    stats.add_event(event)
    report = format_json_report(stats.to_dict())

    assert "ядро" in report


# 6. Integration test CLI с временным каталогом
def test_cli_output_file(tmp_path, monkeypatch):
    log_file = tmp_path / "events.jsonl"
    out_file = tmp_path / "report.json"

    log_file.write_text('{"timestamp": "2026-01-01T10:00:00", "level": "CRITICAL", "source": "core", "message": "crash"}\n', encoding="utf-8")

    monkeypatch.setattr(sys, "argv", ["streamstats", str(log_file), "-o", str(out_file)])
    main()

    result = json.loads(out_file.read_text(encoding="utf-8"))
    assert result["total_events"] == 1
    assert result["levels"]["CRITICAL"] == 1


def test_cli_skip_invalid_flag(tmp_path, monkeypatch):
    log_file = tmp_path / "events.jsonl"
    out_file = tmp_path / "report.json"

    log_file.write_text(
        '{"timestamp": "2026-01-01T10:00:00", "level": "INFO", "source": "web", "message": "ok"}\n'
        'bad_line\n',
        encoding="utf-8",
    )

    monkeypatch.setattr(sys, "argv", ["streamstats", str(log_file), "--skip-invalid", "-o", str(out_file)])
    main()

    result = json.loads(out_file.read_text(encoding="utf-8"))
    assert result["total_events"] == 1
    assert result["skipped_events"] == 1