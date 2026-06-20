from dataclasses import dataclass


@dataclass
class Quote:
    """Котировка — цена закрытия на заданную дату."""

    date: int
    """Дата (Unix timestamp)."""

    close: float
    """Цена закрытия."""

    source: str
    """Источник данных (например, 'bybit', 'coinmetrics')."""

    created_at: int
    """Время создания записи (Unix timestamp)."""