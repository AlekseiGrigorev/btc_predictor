"""
Скрипт первичной загрузки истории BTCUSDT с Bybit в базу данных.

Использует BybitFetcher для загрузки данных с 1 января 2020 года
и сохраняет их через upsert_data.
"""

from datetime import datetime
from app.db import init_db
from app.services.storage import upsert_data
from app.services.fetchers.bybit import BybitFetcher

print("🚀 Инициализация базы данных SQLite...")
try:
    init_db()
    print("✅ База данных успешно инициализирована (файл data/stocks.db).")
except Exception as e:
    print(f"❌ Ошибка при инициализации БД: {e}")
    exit(1)

# Начальная дата: 1 января 2020
start_date = datetime(2020, 1, 1)
end_date = datetime.now()

print(f"📥 Загружаем историю BTC с {start_date.date()} по {end_date.date()}...")

fetcher = BybitFetcher()
df = fetcher.fetch(start_date, end_date)

if df.empty:
    print("⚠️ Данных не получено.")
    exit(0)

print(f"✅ Готово: {len(df)} строк")
print(f"📊 Диапазон: {datetime.fromtimestamp(df['date'].iloc[0]).date()} — {datetime.fromtimestamp(df['date'].iloc[-1]).date()}")
print(df.head())

# Сохраняем в таблицу
upsert_data(df)
print("💾 Данные сохранены в БД")