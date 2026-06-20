from .base import BaseNormalizer


class CumulativeReturnNormalizer(BaseNormalizer):
    """
    Normalizer that computes cumulative returns-based normalization:
    cum_ret[i] = prod(1 + returns[1:i+1]) - 1
    where returns[k] = (price[k] - price[k-1]) / price[k-1]
    """

    def normalize(self, prices: list[float]) -> list[float]:
        """
        Normalize prices via cumulative percentage returns.

        Args:
            prices: List of price values.

        Returns:
            List of normalized values where the first element is 0.0
            and subsequent elements are cumulative returns from the start.
        """
        if len(prices) <= 1:
            return [0.0] * len(prices)
        
        cumulative_returns: list[float] = [0.0]
        cum_product = 1.0  # начинаем с 1.0, так как (1 + 0) = 1
        
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i - 1]) / prices[i - 1]
            cum_product *= (1.0 + ret)
            cumulative_returns.append(cum_product - 1.0)
        
        return cumulative_returns