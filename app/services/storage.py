"""
Модуль для хранения и извлечения данных котировок из SQLite.

Содержит класс TimeframeStorage, который параметризуется таймфреймом
и работает с соответствующей таблицей в БД.
"""

import pandas as pd
from datetime import datetime
from typing import Optional
from app.db import get_connection, get_table_name


def _to_timestamp(series: pd.Series) -> pd.Series:
    """Преобразует колонку с датами в целочисленный Unix timestamp (секунды)."""
    # Если уже числовой — оставляем как есть
    if pd.api.types.is_integer_dtype(series):
        return series
    # Если datetime — конвертируем
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.astype('int64') // 10**9
    # Если строка — парсим
    return pd.to_datetime(series).astype('int64') // 10**9


def _to_datetime(series: pd.Series) -> pd.Series:
    """
    Преобразует колонку с Unix timestamp (секунды) в datetime.

    Args:
        series: Серия с целочисленными Unix timestamp.

    Returns:
        Серия с datetime значениями.
    """
    return pd.to_datetime(series.astype(float), unit='s')


class TimeframeStorage:
    """
    Класс для работы с таблицей котировок определённого таймфрейма.

    Позволяет вставлять, обновлять и извлекать данные из соответствующей
    таблицы в SQLite.

    Attributes:
        timeframe: Ключ таймфрейма (например, '1d', '4h', '1h').
        table_name: Имя таблицы в БД.
    """

    def __init__(self, timeframe: str) -> None:
        """
        Инициализация хранилища для указанного таймфрейма.

        Args:
            timeframe: Ключ таймфрейма (например, '1d', '4h', '1h').

        Raises:
            ValueError: Если таймфрейм не поддерживается.
        """
        self.timeframe = timeframe
        self.table_name = get_table_name(timeframe)

    def upsert_data(self, df: pd.DataFrame) -> None:
        """
        Вставка или обновление записей в таблице.

        Выполняет UPSERT: существующие записи (по дате) обновляются,
        новые — добавляются.

        Args:
            df: DataFrame с колонками date, close, source, created_at.
        """
        df = df.copy()
        df = df.drop_duplicates(subset=['date']).copy()
        df = df.assign(date=_to_timestamp(df['date']))
        if 'created_at' in df.columns:
            df = df.assign(created_at=_to_timestamp(df['created_at']))

        with get_connection() as conn:
            # Создаем временную таблицу с данными
            df.to_sql('temp_table', conn, if_exists='replace', index=False)

            # Обновляем существующие записи
            conn.execute(f"""
                UPDATE {self.table_name}
                SET close = temp.close, source = temp.source, created_at = temp.created_at
                FROM temp_table temp
                WHERE {self.table_name}.date = temp.date
            """)

            # Вставляем новые
            conn.execute(f"""
                INSERT INTO {self.table_name}(date, close, source, created_at)
                SELECT date, close, source, created_at FROM temp_table
                WHERE date NOT IN (SELECT date FROM {self.table_name})
            """)

            conn.execute("DROP TABLE temp_table")

    def get_min_date(self) -> Optional[datetime]:
        """
        Возвращает минимальное значение поля date из таблицы (datetime).

        Returns:
            datetime или None, если таблица пуста.
        """
        with get_connection() as conn:
            result = conn.execute(
                f"SELECT MIN(date) FROM {self.table_name}"
            ).fetchone()
            return datetime.fromtimestamp(result[0]) if result and result[0] is not None else None

    def get_max_date(self) -> Optional[datetime]:
        """
        Возвращает максимальное значение поля date из таблицы (datetime).

        Returns:
            datetime или None, если таблица пуста.
        """
        with get_connection() as conn:
            result = conn.execute(
                f"SELECT MAX(date) FROM {self.table_name}"
            ).fetchone()
            return datetime.fromtimestamp(result[0]) if result and result[0] is not None else None

    def get_last_records(self, n: int) -> pd.DataFrame:
        """
        Возвращает последние n записей из таблицы, отсортированных по возрастанию даты.

        Args:
            n: Количество записей.

        Returns:
            DataFrame с колонками date (index) и close.
        """
        query = f"""
            SELECT date, close
            FROM {self.table_name}
            ORDER BY date DESC
            LIMIT ?
        """
        with get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=(n,))

        if not df.empty:
            df = df.iloc[::-1].reset_index(drop=True)
            # Конвертируем Unix timestamp в datetime
            df = df.assign(date=_to_datetime(df['date']))
            df.set_index('date', inplace=True)

        return df

    def get_all_records(self) -> pd.DataFrame:
        """
        Возвращает все записи из таблицы, отсортированных по возрастанию даты.

        Returns:
            DataFrame с колонками date (index) и close.
        """
        query = f"""
            SELECT date, close
            FROM {self.table_name}
            ORDER BY date
        """
        with get_connection() as conn:
            df = pd.read_sql_query(query, conn)

        if not df.empty:
            # Конвертируем Unix timestamp в datetime
            df = df.assign(date=_to_datetime(df['date']))
            df.set_index('date', inplace=True)

        return df