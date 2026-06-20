from dtw import dtw as compute_dtw
import pandas as pd

from app.models.sequence import Sequence
from app.services.predictors.base import BasePredictor
from app.services.storage import TimeframeStorage
from app.services.transformer import Transformer
from app.services.normalizers.return_based import ReturnBasedNormalizer


class DTWPredictor(BasePredictor):
    """
    Предсказатель на основе DTW (Dynamic Time Warping).

    Работает с таблицей дневных котировок (таймфрейм 1d).
    """

    def __init__(self, timeframe: str = "1d") -> None:
        """
        Args:
            timeframe: Таймфрейм для анализа (по умолчанию '1d').
        """
        self.timeframe = timeframe

    def predict(self) -> Sequence:
        """
        Выполнить предсказание на основе DTW.

        Returns:
            Sequence с последовательностью цен закрытия.

        Raises:
            ValueError: Если в БД нет данных или недостаточно записей.
        """
        storage = TimeframeStorage(self.timeframe)

        # Получаем минимальную дату из таблицы (datetime)
        min_date = storage.get_min_date()
        if min_date is None:
            raise ValueError("В БД нет данных для предсказания")

        # Получаем все записи из таблицы
        df = storage.get_all_records()
        if len(df) < 30:
            raise ValueError(
                f"Недостаточно данных: требуется 30 записей, доступно {len(df)}"
            )

        # Извлекаем первые и последние 30 записей из всего множества
        first_30 = df['close'].iloc[:30].tolist()
        last_30 = df['close'].iloc[-30:].tolist()

        # Нормализуем обе последовательности через возвратный нормализатор
        normalizer = ReturnBasedNormalizer()
        first_norm = normalizer.normalize(first_30)
        last_norm = normalizer.normalize(last_30)

        # Вычисляем DTW-дистанцию между первой и последней последовательностями
        distance = compute_dtw(first_norm, last_norm).distance

        # Выводим результат
        print(f"DTW-дистанция между первыми и последними 30 записями: {distance:.6f}")

        # Преобразуем первые 30 записей в последовательность
        sequence = Transformer.transform_to_sequence(df, min_date, 30)

        return sequence
