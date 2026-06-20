from datetime import datetime
from app.db import init_db
from app.services.storage import upsert_data
from app.services.fetchers.coinmetrics import CoinMetricsFetcher

print("🚀 Инициализация базы данных SQLite...")
try:
    init_db()
    print("✅ База данных успешно инициализирована (файл data/stocks.db).")
except Exception as e:
    print(f"❌ Ошибка при инициализации БД: {e}")
    exit(1)

# Загружаем все доступные данные CoinMetrics
fetcher = CoinMetricsFetcher()
result = fetcher.fetch(
    start_date=datetime(2009, 1, 1),
    end_date=datetime.now(),
)

# Вставим в таблицу
upsert_data(result)