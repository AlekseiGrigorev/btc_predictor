import time
import pandas as pd
from datetime import datetime

from app.services.fetchers.base import BaseFetcher


class CoinMetricsFetcher(BaseFetcher):
    """Фетчер для получения исторических цен BTC с CoinMetrics."""

    def __init__(
        self,
        timeframe: str = "1d",
        url: str = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv",
    ):
        """
        Инициализация фетчера CoinMetrics.

        Args:
            timeframe: Ключ таймфрейма (по умолчанию '1d' — только дневные данные).
            url: URL к CSV-файлу с данными.
        """
        super().__init__(timeframe)

        if timeframe != "1d":
            raise ValueError(
                f"CoinMetricsFetcher поддерживает только таймфрейм '1d' (дневные данные). "
                f"Получен: '{timeframe}'."
            )

        self.url = url

    def fetch(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Загрузка данных CoinMetrics в заданном диапазоне дат.

        Аргументы:
            start_date: Начальная дата (включительно).
            end_date: Конечная дата (включительно).

        Возвращает:
            DataFrame с колонками: date, close, source, created_at
        """
        print(f"📥 Загрузка данных CoinMetrics с {self.url}...")

        # Загружаем CSV-файл (time парсится как datetime, PriceUSD как float)
        df = pd.read_csv(self.url, parse_dates=["time"])

        # Убираем строки, где нет времени или цены
        rows_before = len(df)
        df = df.dropna(subset=["time", "PriceUSD"])
        rows_after = len(df)
        dropped = rows_before - rows_after
        if dropped:
            print(f"  ⚠️  Удалено {dropped} строк с пропущенными значениями")

        # Собираем итоговый DataFrame с явным приведением типов
        result = pd.DataFrame({
            "date": df["time"].astype("int64") // 10**9,
            "close": df["PriceUSD"].astype(float),
        })

        # Фильтруем по запрошенному диапазону дат
        start_ts = int(start_date.timestamp())
        end_ts = int(end_date.timestamp())
        result = result[(result["date"] >= start_ts) & (result["date"] <= end_ts)]

        # Сортируем по возрастанию даты
        result = result.sort_values("date").reset_index(drop=True)

        # Добавляем служебные колонки
        result["source"] = "coinmetrics"
        result["created_at"] = int(time.time())

        # Логируем результат
        print(f"  ✅ Загружено {len(result)} строк")
        if len(result) > 0:
            print(
                f"  📅 Диапазон: {datetime.fromtimestamp(result['date'].iloc[0]).date()}"
                f" — {datetime.fromtimestamp(result['date'].iloc[-1]).date()}"
            )
        else:
            print("  ⚠️  Нет данных в указанном диапазоне дат")

        # Возвращаем только нужные колонки
        return result[["date", "close", "source", "created_at"]]