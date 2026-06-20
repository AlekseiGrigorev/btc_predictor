from typing import List
from datetime import datetime

import pandas as pd

from app.models.sequence import Sequence


class Transformer:
    """Преобразователь данных для подготовки последовательностей из DataFrame."""

    @staticmethod
    def transform_to_sequence(df: pd.DataFrame, date: datetime, window_size: int) -> Sequence:
        """
        Извлекает из DataFrame окно значений размера window_size, начиная с указанной даты,
        и возвращает последовательность Sequence.

        Args:
            df: DataFrame с колонкой 'close' и DatetimeIndex.
            date: Начальная дата окна (включительно).
            window_size: Размер окна (количество последовательных записей).

        Returns:
            Sequence с date_start, равной фактической начальной дате окна (ближайшая
            существующая в индексе дата >= переданной date), date_end — датой последнего
            значения в окне, и списком значений close в окне.

        Raises:
            ValueError: Если DataFrame пуст, отсутствует колонка 'close',
                        индекс не DatetimeIndex или не хватает данных.
        """
        if df.empty:
            raise ValueError("DataFrame пуст")

        if 'close' not in df.columns:
            raise ValueError("DataFrame должен содержать колонку 'close'")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame должен иметь DatetimeIndex")

        # Определяем позицию ближайшей даты >= переданной
        start_idx = df.index.searchsorted(date)

        # Фактическая дата начала окна (может отличаться, если переданная дата отсутствует в индексе)
        actual_start_date = df.index[start_idx].to_pydatetime()

        end_idx = start_idx + window_size

        # Проверяем, что в DataFrame достаточно данных для окна
        if end_idx > len(df):
            raise ValueError(
                f"Недостаточно данных: начиная с {date} требуется {window_size} записей, "
                f"но доступно только {len(df) - start_idx}"
            )

        # Выбираем срез и формируем последовательность
        window_values = df.iloc[start_idx:end_idx]['close'].tolist()

        # Дата последнего элемента окна
        end_date = df.index[end_idx - 1].to_pydatetime()

        return Sequence(date_start=actual_start_date, date_end=end_date, values=window_values)

    @staticmethod
    def transform_last_to_sequence(df: pd.DataFrame, window_size: int) -> Sequence:
        """
        Преобразует последние window_size записей DataFrame в последовательность Sequence.

        Args:
            df: DataFrame с колонкой 'close' и DatetimeIndex.
            window_size: Размер окна (количество последних записей).

        Returns:
            Sequence с date_start, равной дате самого раннего элемента окна,
            date_end — датой последнего элемента окна, и списком значений close.

        Raises:
            ValueError: Если DataFrame пуст, отсутствует колонка 'close',
                        индекс не DatetimeIndex или не хватает данных.
        """
        if df.empty:
            raise ValueError("DataFrame пуст")

        if 'close' not in df.columns:
            raise ValueError("DataFrame должен содержать колонку 'close'")

        if not isinstance(df.index, pd.DatetimeIndex):
            raise ValueError("DataFrame должен иметь DatetimeIndex")

        if len(df) < window_size:
            raise ValueError(
                f"Недостаточно данных: требуется {window_size} записей, "
                f"но доступно только {len(df)}"
            )

        # Берём последние window_size строк
        window_df = df.iloc[-window_size:]

        # Дата самого раннего элемента окна
        start_date = window_df.index[0].to_pydatetime()

        # Дата последнего элемента окна
        end_date = window_df.index[-1].to_pydatetime()

        # Список значений close
        window_values = window_df['close'].tolist()

        return Sequence(date_start=start_date, date_end=end_date, values=window_values)
