from .base import BaseNormalizer


class CumulativeSumReturnNormalizer(BaseNormalizer):
    """
    Normalizer that computes cumulative sum of returns:
    cum_sum[i] = sum(returns[1:i+1])
    where returns[k] = (price[k] - price[k-1]) / price[k-1]
    """

    def normalize(self, prices: list[float]) -> list[float]:
        """
        Normalize prices via cumulative sum of percentage returns.

        Args:
            prices: List of price values.

        Returns:
            List of normalized values where the first element is 0.0
            and subsequent elements are cumulative sum of returns from the start.
        """
        if len(prices) <= 1:
            return [0.0] * len(prices)
        
        cumulative_sum: list[float] = [0.0]
        sum_returns = 0.0
        
        for i in range(1, len(prices)):
            ret = (prices[i] - prices[i - 1]) / prices[i - 1]
            sum_returns += ret
            cumulative_sum.append(sum_returns)
        
        return cumulative_sum