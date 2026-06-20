from .base import BaseNormalizer


class RetroNormalizer(BaseNormalizer):
    """
    Нормализатор, вычисляющий отношение каждой цены к первой цене:
    price[i] / price[0].
    """

    def normalize(self, prices: list[float]) -> list[float]:
        """
        Нормализация относительно первой цены.

        Args:
            prices: Список цен.

        Returns:
            Список нормализованных значений, где первый элемент равен 1.0.
            Если первая цена равна 0, возвращает список нулей.
        """
        if prices[0] == 0:
            return [0.0] * len(prices)

        normalized = [p / prices[0] for p in prices]
        return normalized