import time
from datetime import datetime, timezone
import requests
import pandas as pd

from app.db import get_binance_interval
from app.services.fetchers.base import BaseFetcher


class BinanceFetcher(BaseFetcher):
    """Фетчер для получения свечей BTCUSDT с Binance через публичный REST API."""

    def __init__(
        self,
        timeframe: str = "1d",
        delay: float = 0.3,
    ):
        """
        Инициализация фетчера Binance.

        Args:
            timeframe: Ключ таймфрейма (например, '1d', '4h', '1h').
            delay: Задержка между запросами в секундах (по умолчанию 1 с).
        """
        super().__init__(timeframe)
        self.symbol = "BTCUSDT"
        self.interval = get_binance_interval(timeframe)
        self.delay = delay
        self.base_url = "https://api.binance.com/api/v3/klines"

    def fetch(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Получение свечей BTCUSDT с Binance в заданном диапазоне дат.

        Аргументы:
            start_date: Начальная дата (включительно).
            end_date: Конечная дата (включительно).

        Возвращает:
            DataFrame с колонками: date, close, source, created_at
        """
        # Binance API ожидает timestamp в миллисекундах
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)

        all_klines: list[list] = []
        existing_timestamps: set[int] = set()
        current_start = start_ms

        # Текущий момент UTC в ms (для проверки остановки)
        now_utc = datetime.now(timezone.utc)
        now_ms = int(now_utc.timestamp() * 1000)

        while True:
            params = {
                "symbol": self.symbol,
                "interval": self.interval,
                "limit": 1000,
                "startTime": current_start,
            }

            response = requests.get(self.base_url, params=params, timeout=30)

            # Проверка на rate limit (HTTP 429)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                print(f"  ⚠️  Rate limit hit, ожидание {retry_after} с...")
                time.sleep(retry_after)
                continue

            response.raise_for_status()
            klines = response.json()

            if not klines:
                print("  ✅ Все данные загружены")
                break

            # Binance возвращает свечи от старых к новым, сортировка не нужна
            # Но фильтруем дубликаты по close_time (индекс 6)
            new_klines = [k for k in klines if int(k[6]) not in existing_timestamps]

            if not new_klines:
                print("  ✅ Все данные загружены (дубликаты)")
                break

            # Добавляем close_time новых свечей в набор
            for k in new_klines:
                existing_timestamps.add(int(k[6]))

            all_klines.extend(new_klines)

            # Выводим прогресс
            oldest_ts = int(new_klines[0][6])
            oldest_date = datetime.fromtimestamp(oldest_ts / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
            latest_ts = int(new_klines[-1][6])
            latest_date = datetime.fromtimestamp(latest_ts / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
            print(f"  📦 {len(new_klines)} свечей: {oldest_date} — {latest_date}")

            # Если последняя свеча — не ранее текущего момента, останавливаемся
            if latest_ts >= now_ms:
                print("  ✅ Дошли до текущего момента")
                break

            # Если дошли до end_date — выходим
            if latest_ts >= end_ms:
                print("  ✅ Достигнут конец запрошенного диапазона")
                break

            # Сдвигаем окно на шаг вперёд (на 1 мс после последней загруженной)
            current_start = latest_ts + 1

            # Задержка для избежания rate limit
            time.sleep(self.delay)

        if not all_klines:
            return pd.DataFrame(
                columns=["date", "close", "source", "created_at"]
            )

        # Структура свечи Binance (klines):
        # [0] open_time, [1] open, [2] high, [3] low, [4] close,
        # [5] volume, [6] close_time, [7] quote_volume,
        # [8] trades, [9] taker_base, [10] taker_quote, [11] ignore

        # Строим DataFrame из сырых данных API
        raw = pd.DataFrame(
            all_klines,
            columns=[
                "open_time", "open", "high", "low", "close", "volume",
                "close_time", "quote_volume", "trades", "taker_base",
                "taker_quote", "ignore",
            ],
        )

        # Собираем итоговый DataFrame:
        # date = close_time в секундах, округлённый вверх до целого часа
        # (Binance возвращает close_time с 59 секундами, исправляем это)
        df = pd.DataFrame({
            "date": ((raw["close_time"].astype(int) // 1000 + 3599) // 3600) * 3600,
            "close": raw["close"].astype(float),
        })

        # Фильтруем по запрошенному диапазону дат (на случай, если API вернул лишнее)
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())
        df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)]

        # Сортируем по возрастанию даты (сначала старые)
        df = df.sort_values("date").reset_index(drop=True)

        # Добавляем служебные колонки
        df["source"] = "binance"
        df["created_at"] = int(time.time())

        # Возвращаем только нужные колонки
        return df[["date", "close", "source", "created_at"]]