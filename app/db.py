import sqlite3
from pathlib import Path

# Путь к файлу БД (создастся в папке data)
DB_PATH = Path(__file__).parent.parent / "data" / "stocks.db"
DB_PATH.parent.mkdir(exist_ok=True)

# Словарь доступных таймфреймов: ключ — идентификатор, значение — имя таблицы в БД
TIMEFRAMES: dict[str, str] = {
    "1d": "quotes_1d",
    "4h": "quotes_4h",
    "1h": "quotes_1h",
}

# Маппинг таймфреймов в интервалы Bybit API
TIMEFRAME_TO_BYBIT_INTERVAL: dict[str, str] = {
    "1d": "D",
    "4h": "240",
    "1h": "60",
}

# Маппинг таймфреймов в интервалы Binance API
TIMEFRAME_TO_BINANCE_INTERVAL: dict[str, str] = {
    "1d": "1d",
    "4h": "4h",
    "1h": "1h",
}


def get_table_name(timeframe: str) -> str:
    """
    Возвращает имя таблицы для указанного таймфрейма.

    Args:
        timeframe: Ключ таймфрейма (например, '1d', '4h', '1h').

    Returns:
        Имя таблицы в БД.

    Raises:
        ValueError: Если таймфрейм не поддерживается.
    """
    if timeframe not in TIMEFRAMES:
        raise ValueError(
            f"Неподдерживаемый таймфрейм '{timeframe}'. "
            f"Доступны: {', '.join(TIMEFRAMES.keys())}"
        )
    return TIMEFRAMES[timeframe]


def get_binance_interval(timeframe: str) -> str:
    """
    Возвращает интервал Binance API для указанного таймфрейма.

    Args:
        timeframe: Ключ таймфрейма (например, '1d', '4h', '1h').

    Returns:
        Строка интервала для Binance API.
    """
    if timeframe not in TIMEFRAME_TO_BINANCE_INTERVAL:
        raise ValueError(
            f"Неподдерживаемый таймфрейм '{timeframe}'. "
            f"Доступны: {', '.join(TIMEFRAME_TO_BINANCE_INTERVAL.keys())}"
        )
    return TIMEFRAME_TO_BINANCE_INTERVAL[timeframe]


def get_bybit_interval(timeframe: str) -> str:
    """
    Возвращает интервал Bybit API для указанного таймфрейма.

    Args:
        timeframe: Ключ таймфрейма (например, '1d', '4h', '1h').

    Returns:
        Строка интервала для Bybit API.
    """
    if timeframe not in TIMEFRAME_TO_BYBIT_INTERVAL:
        raise ValueError(
            f"Неподдерживаемый таймфрейм '{timeframe}'. "
            f"Доступны: {', '.join(TIMEFRAME_TO_BYBIT_INTERVAL.keys())}"
        )
    return TIMEFRAME_TO_BYBIT_INTERVAL[timeframe]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Позволяет обращаться к колонкам по имени: row['close']
    conn.execute("PRAGMA journal_mode=WAL")  # Оптимизация для конкурентных чтений
    return conn


def _migrate_old_table(conn: sqlite3.Connection) -> None:
    """
    Миграция: переименовывает старую таблицу 'quotes' в 'quotes_1d'.

    Если таблица 'quotes' существует, а 'quotes_1d' — нет, то данные
    переносятся в новую таблицу.
    """
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotes'")
    has_old = cursor.fetchone() is not None

    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='quotes_1d'")
    has_new = cursor.fetchone() is not None

    if has_old and not has_new:
        print("[migrate] Обнаружена старая таблица 'quotes'. Переименовываю в 'quotes_1d'...")
        conn.execute("ALTER TABLE quotes RENAME TO quotes_1d")
        print("[migrate] Готово.")
    elif has_old and has_new:
        print("[migrate] Старая таблица 'quotes' существует, но 'quotes_1d' уже есть. Пропускаю.")


def init_db():
    """Создаёт таблицы для всех таймфреймов, если их ещё нет"""
    with get_connection() as conn:
        _migrate_old_table(conn)
        for table_name in TIMEFRAMES.values():
            conn.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    date INTEGER PRIMARY KEY,
                    close REAL,
                    source TEXT,
                    created_at INTEGER
                )
            """)
        print(f"[init_db] Созданы таблицы: {', '.join(TIMEFRAMES.values())}")
