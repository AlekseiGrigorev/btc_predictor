"""
Скрипт обновления дневных котировок BTC в БД.

Загружает данные из Bybit с последней имеющейся даты по текущий момент включительно.

Использование:
    python update_1d.py
"""

from app.services import QuotesManager


def main() -> None:
    """Основная функция обновления дневных свечей."""
    print("🚀 Обновление дневных котировок BTCUSDT...")
    try:
        manager = QuotesManager(timeframe="1d")
        count = manager.update_quotes()
        print(f"✅ Загружено: {count} записей")
    except ValueError as e:
        print(f"❌ Ошибка: {e}")
        exit(1)
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        exit(1)


if __name__ == "__main__":
    main()