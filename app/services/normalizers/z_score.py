import math

from .base import BaseNormalizer


class ZScoreNormalizer(BaseNormalizer):
    """
    Нормализатор, выполняющий Z-score стандартизацию:
    (price - mean) / std.
    """

    def normalize(self, prices: list[float]) -> list[float]:
        """
        Стандартизация методом Z-score.

        Args:
            prices: Список цен.

        Returns:
            Список стандартизированных значений.
            Если среднеквадратичное отклонение равно 0, возвращает список нулей.
        """
        mean_price = sum(prices) / len(prices)
        variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
        std_price = math.sqrt(variance)

        if std_price == 0:
            return [0.0] * len(prices)

        normalized = [(p - mean_price) / std_price for p in prices]
        return normalized