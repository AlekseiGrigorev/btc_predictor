import time
from datetime import datetime, timezone
import pandas as pd
from pybit.unified_trading import HTTP

from app.db import get_bybit_interval
from app.services.fetchers.base import BaseFetcher


class BybitFetcher(BaseFetcher):
    """Фетчер для получения свечей BTCUSDT с Bybit для указанного таймфрейма."""

    def __init__(
        self,
        timeframe: str = "1d",
        symbol: str = "BTCUSDT",
        testnet: bool = False,
        timeout: int = 30,
        delay: float = 0.3,
    ):
        """
        Инициализация фетчера Bybit.

        Args:
            timeframe: Ключ таймфрейма (например, '1d', '4h', '1h').
            symbol: Торговая пара (по умолчанию 'BTCUSDT').
            testnet: Использовать тестовую сеть.
            timeout: Таймаут запроса в секундах.
            delay: Задержка между запросами в секундах (по умолчанию 0.3).
        """
        super().__init__(timeframe)
        self.symbol = symbol
        self.interval = get_bybit_interval(timeframe)
        self.client = HTTP(testnet=testnet, timeout=timeout)
        self.delay = delay

    def fetch(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Получение дневных свечей BTCUSDT с Bybit в заданном диапазоне дат.

        Аргументы:
            start_date: Начальная дата (включительно).
            end_date: Конечная дата (включительно).

        Возвращает:
            DataFrame с колонками: date, close, source, created_at
        """
        # Bybit API ожидает timestamp в миллисекундах
        start_ms = int(start_date.timestamp() * 1000)
        end_ms = int(end_date.timestamp() * 1000)

        all_klines: list[list] = []
        existing_timestamps: set[int] = set()
        current_start = start_ms

        # Текущий момент UTC в ms (для проверки остановки)
        now_utc = datetime.now(timezone.utc)
        now_ms = int(now_utc.timestamp() * 1000)

        while True:
            response = self.client.get_kline(
                symbol=self.symbol,
                interval=self.interval,
                limit=1000,
                start=current_start,
            )
            klines = response.get("result", {}).get("list", [])

            if not klines:
                print("  ✅ Все данные загружены")
                break

            # Bybit возвращает свечи от новых к старым, поэтому разворачиваем
            klines.sort(key=lambda x: int(x[0]))

            # Фильтруем дубликаты
            new_klines = [k for k in klines if int(k[0]) not in existing_timestamps]

            if not new_klines:
                print("  ✅ Все данные загружены (дубликаты)")
                break

            # Добавляем timestamp'ы новых свечей в набор
            for k in new_klines:
                existing_timestamps.add(int(k[0]))

            all_klines.extend(new_klines)

            # Выводим прогресс
            oldest_ts = int(new_klines[0][0])
            oldest_date = datetime.fromtimestamp(oldest_ts / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
            latest_ts = int(new_klines[-1][0])
            latest_date = datetime.fromtimestamp(latest_ts / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M')
            print(f"  📦 {len(new_klines)} свечей: {oldest_date} — {latest_date}")

            # Если последняя свеча — не ранее текущего момента, останавливаемся
            # Это корректно для любых таймфреймов (1d, 4h, 1h)
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

            # Проверяем подсказку от API об ограничении частоты запросов
            ret_msg = response.get("ret_msg", "") or ""
            if "rate" in ret_msg.lower():
                print("  [BybitFetcher] Rate limit hit, sleeping 2s...")
                time.sleep(2)

        if not all_klines:
            return pd.DataFrame(
                columns=["date", "close", "source", "created_at"]
            )

        # Строим DataFrame из сырых данных API
        raw = pd.DataFrame(
            all_klines,
            columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"],
        )

        # Собираем итоговый DataFrame без лишних преобразований:
        # timestamp в ms → делим на 1000, получаем секунды
        df = pd.DataFrame({
            "date": raw["timestamp"].astype(int) // 1000,
            "close": raw["close"].astype(float),
        })

        # Фильтруем по запрошенному диапазону дат (на случай, если API вернул лишнее)
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())
        df = df[(df["date"] >= start_ts) & (df["date"] <= end_ts)]

        # Сортируем по возрастанию даты (сначала старые)
        df = df.sort_values("date").reset_index(drop=True)

        # Добавляем служебные колонки
        df["source"] = "bybit"
        df["created_at"] = int(time.time())

        # Возвращаем только нужные колонки
        return df[["date", "close", "source", "created_at"]]