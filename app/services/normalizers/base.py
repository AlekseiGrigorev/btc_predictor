from abc import ABC, abstractmethod


class BaseNormalizer(ABC):
    """Abstract base class for price normalizers."""

    @abstractmethod
    def normalize(self, prices: list[float]) -> list[float]:
        """
        Normalize a list of price values.

        Args:
            prices: List of price values.

        Returns:
            List of normalized values of the same length.
        """
        pass