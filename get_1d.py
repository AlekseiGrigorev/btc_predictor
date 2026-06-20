"""
Скрипт первичной загрузки дневных свечей BTC в базу данных.

Сначала загружает исторические данные из CoinMetrics (все доступные),
затем догружает данные с Bybit (с 1 января 2020).
Данные сохраняются через upsert_data (без дубликатов).
"""

from datetime import datetime
from app.db import init_db
from app.services.storage import TimeframeStorage
from app.services.fetchers.coinmetrics import CoinMetricsFetcher
from app.services.fetchers.bybit import BybitFetcher


def main() -> None:
    """Основная функция загрузки дневных свечей."""
    # 1. Инициализация БД
    print("🚀 Инициализация базы данных SQLite...")
    try:
        init_db()
        print("✅ База данных успешно инициализирована (файл data/stocks.db).")
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        exit(1)

    # 2. Загрузка дневных данных из CoinMetrics (глубокая история)
    print("\n" + "=" * 60)
    print("📥 Шаг 1: Загрузка исторических данных CoinMetrics")
    print("=" * 60)
    try:
        coinmetrics_fetcher = CoinMetricsFetcher(timeframe="1d")
        coinmetrics_result = coinmetrics_fetcher.fetch(
            start_date=datetime(2009, 1, 1),
            end_date=datetime.now(),
        )
        if not coinmetrics_result.empty:
            TimeframeStorage(timeframe="1d").upsert_data(coinmetrics_result)
            print(f"💾 CoinMetrics: сохранено {len(coinmetrics_result)} строк")
        else:
            print("⚠️ CoinMetrics: нет данных для сохранения")
    except Exception as e:
        print(f"❌ Ошибка при загрузке CoinMetrics: {e}")
        exit(1)

    # 3. Загрузка дневных данных из Bybit (с 2020 года)
    print("\n" + "=" * 60)
    print("📥 Шаг 2: Загрузка дневных данных Bybit")
    print("=" * 60)
    start_date = datetime(2020, 1, 1)
    end_date = datetime.now()
    try:
        bybit_fetcher = BybitFetcher(timeframe="1d")
        bybit_result = bybit_fetcher.fetch(start_date, end_date)
        if not bybit_result.empty:
            TimeframeStorage(timeframe="1d").upsert_data(bybit_result)
            print(f"💾 Bybit: сохранено {len(bybit_result)} строк")
        else:
            print("⚠️ Bybit: нет данных для сохранения")
    except Exception as e:
        print(f"❌ Ошибка при загрузке Bybit: {e}")
        exit(1)

    # 4. Итог
    print("\n" + "=" * 60)
    print("✅ Загрузка дневных свечей завершена!")
    total_coinmetrics = len(coinmetrics_result) if not coinmetrics_result.empty else 0
    total_bybit = len(bybit_result) if not bybit_result.empty else 0
    print(f"   CoinMetrics: {total_coinmetrics} строк")
    print(f"   Bybit:       {total_bybit} строк")
    print(f"   Всего:       {total_coinmetrics + total_bybit} строк")
    print("=" * 60)


if __name__ == "__main__":
    main()