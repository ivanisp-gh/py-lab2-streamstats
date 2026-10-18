class StreamStatsError(Exception):
    """Базовая ошибка пакета streamstats."""
    pass


class UnsupportedFormatError(StreamStatsError):
    """Неподдерживаемый формат файла."""
    pass


class InvalidEventError(StreamStatsError):
    """Неверное событие или отсутствие обязательных полей."""
    pass


class InvalidTimestampError(StreamStatsError):
    """Неверная временная метка."""
    pass


class CLIConfigError(StreamStatsError):
    """Ошибка конфигурации CLI."""
    pass