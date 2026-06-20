"""
Скрипт первичной загрузки 1-часовых свечей BTC в базу данных.

Сначала загружает исторические данные из Binance (с 1 января 2017),
затем догружает данные с Bybit (с 1 января 2020).
Данные сохраняются через upsert_data (без дубликатов).
"""

from datetime import datetime
from app.db import init_db
from app.services.storage import TimeframeStorage
from app.services.fetchers.binance import BinanceFetcher
from app.services.fetchers.bybit import BybitFetcher


def main() -> None:
    """Основная функция загрузки 1-часовых свечей."""
    # 1. Инициализация БД
    print("🚀 Инициализация базы данных SQLite...")
    try:
        init_db()
        print("✅ База данных успешно инициализирована (файл data/stocks.db).")
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        exit(1)

    # 2. Загрузка 1-часовых данных из Binance (с 2017 года)
    print("\n" + "=" * 60)
    print("📥 Шаг 1: Загрузка 1-часовых данных Binance")
    print("=" * 60)
    try:
        binance_fetcher = BinanceFetcher(timeframe="1h")
        binance_result = binance_fetcher.fetch(
            start_date=datetime(2017, 1, 1),
            end_date=datetime.now(),
        )
        if not binance_result.empty:
            TimeframeStorage(timeframe="1h").upsert_data(binance_result)
            print(f"💾 Binance: сохранено {len(binance_result)} строк")
        else:
            print("⚠️ Binance: нет данных для сохранения")
    except Exception as e:
        print(f"❌ Ошибка при загрузке Binance: {e}")
        exit(1)

    # 3. Загрузка 1-часовых данных из Bybit (с 2020 года)
    print("\n" + "=" * 60)
    print("📥 Шаг 2: Загрузка 1-часовых данных Bybit")
    print("=" * 60)
    try:
        bybit_fetcher = BybitFetcher(timeframe="1h")
        bybit_result = bybit_fetcher.fetch(
            start_date=datetime(2020, 1, 1),
            end_date=datetime.now(),
        )
        if not bybit_result.empty:
            TimeframeStorage(timeframe="1h").upsert_data(bybit_result)
            print(f"💾 Bybit: сохранено {len(bybit_result)} строк")
        else:
            print("⚠️ Bybit: нет данных для сохранения")
    except Exception as e:
        print(f"❌ Ошибка при загрузке Bybit: {e}")
        exit(1)

    # 4. Итог
    print("\n" + "=" * 60)
    print("✅ Загрузка 1-часовых свечей завершена!")
    total_binance = len(binance_result) if not binance_result.empty else 0
    total_bybit = len(bybit_result) if not bybit_result.empty else 0
    print(f"   Binance: {total_binance} строк")
    print(f"   Bybit:   {total_bybit} строк")
    print(f"   Всего:   {total_binance + total_bybit} строк")
    print("=" * 60)


if __name__ == "__main__":
    main()