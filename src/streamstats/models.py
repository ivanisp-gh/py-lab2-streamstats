from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True) # не будет хранится словарь в памяти
class LogEvent:
    timestamp: datetime
    level: str
    source: str
    message: str