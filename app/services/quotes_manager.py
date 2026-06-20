"""
Менеджер для работы с котировками криптовалют.

Содержит логику обновления котировок в БД для разных таймфреймов.
"""

from datetime import datetime
from app.services.storage import TimeframeStorage
from app.services.fetchers.bybit import BybitFetcher
from app.db import init_db


class QuotesManager:
    """Класс для управления загрузкой и обновлением котировок."""

    def __init__(self, timeframe: str = "1d") -> None:
        """
        Инициализация менеджера котировок для указанного таймфрейма.

        Args:
            timeframe: Ключ таймфрейма (например, '1d', '4h', '1h').
                      По умолчанию '1d' для обратной совместимости.
        """
        self.timeframe = timeframe
        self.storage = TimeframeStorage(timeframe)

    def update_quotes(self) -> int:
        """
        Обновление котировок в БД для текущего таймфрейма.

        Загружает данные из Bybit с последней имеющейся даты
        по текущий момент включительно. Если в БД нет данных —
        выбрасывает ошибку.

        Returns:
            Количество загруженных записей.
        """
        init_db()

        max_date = self.storage.get_max_date()

        if max_date is None:
            raise ValueError(
                f"База данных для таймфрейма '{self.timeframe}' пуста. "
                "Невозможно определить начальную дату. "
                "Сначала выполните первичную загрузку данных."
            )

        start_date = max_date
        end_date = datetime.now()

        print(
            f"[update_quotes] {self.timeframe}: Загружаем данные с {max_date.strftime('%Y-%m-%d %H:%M')} "
            f"по {end_date.strftime('%Y-%m-%d %H:%M')}"
        )

        fetcher = BybitFetcher(timeframe=self.timeframe)
        df = fetcher.fetch(start_date, end_date)

        if df.empty:
            print(f"[update_quotes] {self.timeframe}: Новых данных нет.")
            return 0

        print(f"[update_quotes] {self.timeframe}: Получено {len(df)} записей. Сохраняем...")
        self.storage.upsert_data(df)
        print(f"[update_quotes] {self.timeframe}: Готово.")

        return len(df)