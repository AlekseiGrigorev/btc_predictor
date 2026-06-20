from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd


class BaseFetcher(ABC):
    """Абстрактный базовый класс для фетчеров рыночных данных."""

    def __init__(self, timeframe: str) -> None:
        """
        Инициализация фетчера для указанного таймфрейма.

        Args:
            timeframe: Ключ таймфрейма (например, '1d', '4h', '1h').
        """
        self.timeframe = timeframe

    @abstractmethod
    def fetch(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Получение рыночных данных в заданном диапазоне дат.

        Аргументы:
            start_date: Начальная дата (включительно).
            end_date: Конечная дата (включительно).

        Возвращает:
            DataFrame с колонками: date, close, source, created_at
        """
        pass
