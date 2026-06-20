from .base import BaseNormalizer


class MinMaxNormalizer(BaseNormalizer):
    """
    Нормализатор, приводящий цены к диапазону [0, 1]
    по формуле Min-Max: (price - min) / (max - min).
    """

    def normalize(self, prices: list[float]) -> list[float]:
        """
        Нормализация методом Min-Max.

        Args:
            prices: Список цен.

        Returns:
            Список нормализованных значений в диапазоне [0, 1].
            Если все цены равны, возвращает список нулей.
        """
        min_price = min(prices)
        max_price = max(prices)

        if max_price == min_price:
            return [0.0] * len(prices)

        normalized = [(p - min_price) / (max_price - min_price) for p in prices]
        return normalized