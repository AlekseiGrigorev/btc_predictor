from dataclasses import dataclass
from datetime import datetime


@dataclass
class Distance:
    """Расстояние между последовательностями на заданную дату."""

    date: datetime
    """Дата, к которой относится расстояние."""

    distance: float
    """Значение расстояния с плавающей точкой."""
