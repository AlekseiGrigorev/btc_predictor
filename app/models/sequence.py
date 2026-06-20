from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class Sequence:
    """Последовательность значений с плавающей точкой на заданный диапазон дат."""

    date_start: datetime
    """Дата начала последовательности."""

    date_end: datetime
    """Дата окончания последовательности."""

    values: List[float]
    """Массив значений с плавающей точкой."""
