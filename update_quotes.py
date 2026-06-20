"""
Скрипт обновления котировок в БД.

Загружает данные из Bybit с последней имеющейся даты по текущий момент включительно.
Поддерживает разные таймфреймы: 1d (по умолчанию), 4h, 1h.

Использование:
    python update_quotes.py              # дневные данные
    python update_quotes.py --timeframe 4h  # 4-часовые данные
    python update_quotes.py --timeframe 1h  # часовые данные
    python update_quotes.py --all           # все таймфреймы
"""

import argparse
from app.services import QuotesManager
from app.db import TIMEFRAMES


def update_quotes(timeframe: str = "1d") -> int:
    """
    Обновление котировок для указанного таймфрейма.

    Args:
        timeframe: Ключ таймфрейма.

    Returns:
        Количество загруженных записей.
    """
    manager = QuotesManager(timeframe=timeframe)
    return manager.update_quotes()


def update_all_timeframes() -> None:
    """Обновление котировок для всех доступных таймфреймов."""
    total = 0
    for timeframe in TIMEFRAMES:
        print(f"\n{'=' * 50}")
        print(f"Обновление таймфрейма: {timeframe}")
        print(f"{'=' * 50}")
        try:
            count = update_quotes(timeframe)
            total += count
            print(f"[{timeframe}] Загружено: {count} записей")
        except ValueError as e:
            print(f"[{timeframe}] Ошибка: {e}")
        except Exception as e:
            print(f"[{timeframe}] Неожиданная ошибка: {e}")
    print(f"\n{'=' * 50}")
    print(f"Всего загружено: {total} записей")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Обновление котировок BTCUSDT из Bybit"
    )
    parser.add_argument(
        "--timeframe",
        type=str,
        default="1d",
        choices=list(TIMEFRAMES.keys()),
        help=f"Таймфрейм для обновления (по умолчанию: 1d). Доступны: {', '.join(TIMEFRAMES.keys())}",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Обновить данные для всех таймфреймов",
    )

    args = parser.parse_args()

    if args.all:
        update_all_timeframes()
    else:
        update_quotes(args.timeframe)