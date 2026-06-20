from abc import ABC, abstractmethod

from app.models.sequence import Sequence


class BasePredictor(ABC):
    """Абстрактный базовый класс для предсказателей."""

    @abstractmethod
    def predict(self) -> Sequence:
        """
        Выполнить предсказание.

        Returns:
            Sequence с результатами предсказания.
        """
        pass
