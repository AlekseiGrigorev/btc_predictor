from .base import BaseNormalizer


class ReturnBasedNormalizer(BaseNormalizer):
    """
    Normalizer that computes returns-based normalization:
    (price[i] - price[i-1]) / price[i-1]
    """

    def normalize(self, prices: list[float]) -> list[float]:
        """
        Normalize prices via percentage returns.

        Args:
            prices: List of price values.

        Returns:
            List of normalized values where the first element is 0.0
            and subsequent elements are (prices[i] - prices[i-1]) / prices[i-1].
        """
        returns: list[float] = []
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i - 1]) / prices[i - 1]
            returns.append(ret)

        # Добавляем 0 для первого элемента
        returns = [0.0] + returns
        return returns