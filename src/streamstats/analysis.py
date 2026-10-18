from collections import Counter
from datetime import datetime
from typing import Optional
from streamstats.models import LogEvent


class StatsAccumulator:
    """Накапливает статистику по логам на лету."""

    def __init__(self) -> None:
        self.total_events: int = 0
        self.skipped_events: int = 0
        self.level_counts: Counter[str] = Counter()
        self.source_counts: Counter[str] = Counter()
        self.error_source_counts: Counter[str] = Counter()
        self.first_time: Optional[datetime] = None # или datatime или none
        self.last_time: Optional[datetime] = None

    def add_event(self, event: LogEvent) -> None:
        """Принимает одно валидное событие и обновляет счетчики."""
        self.total_events += 1

        # Считаем уровни и источники
        self.level_counts[event.level] += 1
        self.source_counts[event.source] += 1

        # Если это ошибка — учитываем источник для топа ошибок
        if event.level in ("ERROR", "CRITICAL"):
            self.error_source_counts[event.source] += 1

        # Обновляем временные границы
        if self.first_time is None or event.timestamp < self.first_time:
            self.first_time = event.timestamp

        if self.last_time is None or event.timestamp > self.last_time:
            self.last_time = event.timestamp

    def add_skipped(self) -> None:
        """Увеличивает счетчик пропущенных битых строк."""
        self.skipped_events += 1

    def get_top_5_error_sources(self) -> list[dict]:
        """Возвращает топ5 источников ошибок."""
        # Сортируем: сначала по числу ошибок убыванию (-count),
        # а если число одинаковое — по алфавиту источника (source)
        sorted_errors = sorted(
            self.error_source_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
        top_5 = sorted_errors[:5]
        return [{"source": src, "count": cnt} for src, cnt in top_5]

    def to_dict(self) -> dict:
        """Формирует итоговый словарь для вывода в JSON."""
        first_iso = self.first_time.isoformat() if self.first_time else None
        last_iso = self.last_time.isoformat() if self.last_time else None

        return {
            "total_events": self.total_events,
            "skipped_events": self.skipped_events,
            "levels": dict(self.level_counts),
            "sources": dict(self.source_counts),
            "top_5_error_sources": self.get_top_5_error_sources(),
            "time_range": {
                "first_event": first_iso,
                "last_event": last_iso,
            },
        }