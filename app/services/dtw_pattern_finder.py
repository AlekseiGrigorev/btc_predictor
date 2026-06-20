import random

from dtw import dtw as compute_dtw
import numpy as np
import pandas as pd

from app.models.distance import Distance
from app.models.sequence import Sequence
from app.services.normalizers.base import BaseNormalizer
from app.services.transformer import Transformer


class DTWPatternFinder:
    """Поиск похожих паттернов в истории цен с использованием DTW (Dynamic Time Warping)."""

    def __init__(self, history: pd.DataFrame, pattern_length: int, normalizer: BaseNormalizer):
        """
        Args:
            history: DataFrame с историческими данными (индекс - дата, колонка 'close').
            pattern_length: длина эталонного паттерна (количество последних значений,
                            которые будут взяты как эталон и отрезаны от истории).
            normalizer: нормализатор для приведения цен к сопоставимому виду.
        """
        self.pattern_length: int = pattern_length
        self.history: pd.DataFrame = history
        self.normalizer: BaseNormalizer = normalizer

        # Проверяем, что истории достаточно (минимум в 2 раза длиннее паттерна)
        if len(self.history) < pattern_length * 2:
            self.history = pd.DataFrame()
            self.reference_pattern = None
            return

        # Создаём эталонный паттерн через Transformer (последние pattern_length записей)
        self.reference_pattern: Sequence = Transformer.transform_last_to_sequence(
            df=self.history,
            window_size=pattern_length
        )
        
        # Нормализуем эталонный паттерн через returns-based normalization
        self.reference_pattern.values = self.normalizer.normalize(self.reference_pattern.values)

        # Отрезаем последние pattern_length записей от истории,
        # чтобы исключить поиск самого себя
        self.history = self.history.iloc[:-pattern_length]

    def find_multiple_patterns(self, top_n: int = 5) -> list[Distance]:
        """
        Находит top_n наиболее похожих паттернов в истории.

        Args:
            top_n: количество паттернов для поиска.

        Returns:
            Список Distance с датой и расстоянием.
        """
        pattern = self.reference_pattern.values
        history_values = self.history['close'].tolist()
        pattern_length = len(pattern)
        distances: list[Distance] = []

        # Перебор всех подпоследовательностей в истории
        for i in range(0, len(history_values) - pattern_length + 1):
            # Извлекаем подпоследовательность
            subsequence = history_values[i:i + pattern_length]
            
            # Нормализуем подпоследовательность через returns-based normalization
            normalized_subsequence = self.normalizer.normalize(subsequence)

            # Вычисляем DTW расстояние
            distance_value = compute_dtw(pattern, normalized_subsequence).distance

            distances.append(
                Distance(date=self.history.index[i], distance=distance_value)
            )

        # Сортируем по расстоянию (чем меньше, тем лучше)
        distances.sort(key=lambda x: x.distance)

        # Возвращаем top_n лучших
        return distances[:top_n]

    def find_patterns_optimized(self, top_n: int = 5, window: int = 10) -> list[Distance]:
        """
        Оптимизированный поиск паттернов.
        
        Примечание: LB_Keogh фильтрация не реализована в текущей версии dtw-python,
        поэтому метод выполняет полный перебор как find_multiple_patterns,
        но с возможностью добавления оптимизаций в будущем.

        Args:
            top_n: количество паттернов для поиска.
            window: размер окна (зарезервировано для будущих оптимизаций).

        Returns:
            Список Distance с датой и расстоянием.
        """
        pattern = self.reference_pattern.values
        history_values = self.history['close'].tolist()
        pattern_length = len(pattern)
        distances: list[Distance] = []

        # Полный перебор всех подпоследовательностей
        for i in range(0, len(history_values) - pattern_length + 1):
            subsequence = history_values[i:i + pattern_length]
            
            # Нормализуем подпоследовательность через returns-based normalization
            normalized_subsequence = self.normalizer.normalize(subsequence)
            
            distance_value = compute_dtw(pattern, normalized_subsequence).distance
            distances.append(
                Distance(date=self.history.index[i], distance=distance_value)
            )

        # Сортируем по расстоянию (чем меньше, тем лучше)
        distances.sort(key=lambda x: x.distance)

        # Возвращаем top_n лучших
        return distances[:top_n]

    def find_distinct_patterns(self, top_n: int = 5, min_gap: int | None = None) -> list[Distance]:
        """
        Находит top_n паттернов с минимальным зазором между индексами.

        Args:
            top_n: количество паттернов для поиска.
            min_gap: минимальный зазор между индексами.
                     Если None, используется длина паттерна.

        Returns:
            Список Distance с датой и расстоянием.
        """
        pattern = self.reference_pattern.values
        history_values = self.history['close'].tolist()
        pattern_length = len(pattern)

        # Если не указан min_gap, используем длину паттерна
        if min_gap is None:
            min_gap = pattern_length

        distances: list[Distance] = []

        # Перебор с шагом = pattern_length (или min_gap)
        for i in range(0, len(history_values) - pattern_length + 1, min_gap):
            subsequence = history_values[i:i + pattern_length]
            
            # Нормализуем подпоследовательность через returns-based normalization
            normalized_subsequence = self.normalizer.normalize(subsequence)
            
            distance_value = compute_dtw(pattern, normalized_subsequence).distance
            distances.append(
                Distance(date=self.history.index[i], distance=distance_value)
            )

        # Сортируем и возвращаем top_n
        distances.sort(key=lambda x: x.distance)
        return distances[:top_n]

    def find_distinct_patterns_filtered(self, top_n: int = 5, min_gap: int | None = None) -> list[Distance]:
        """
        Находит top_n паттернов с post-filtering близких индексов.

        Args:
            top_n: количество паттернов для поиска.
            min_gap: минимальный зазор между индексами.
                     Если None, используется длина паттерна.

        Returns:
            Список Distance с датой и расстоянием.
        """
        pattern = self.reference_pattern.values
        history_values = self.history['close'].tolist()
        pattern_length = len(pattern)

        if min_gap is None:
            min_gap = pattern_length

        # Шаг 1: Находим все паттерны
        all_distances: list[tuple[int, float]] = []
        for i in range(0, len(history_values) - pattern_length + 1):
            subsequence = history_values[i:i + pattern_length]
            
            # Нормализуем подпоследовательность через returns-based normalization
            normalized_subsequence = self.normalizer.normalize(subsequence)
            
            distance = compute_dtw(pattern, normalized_subsequence, distance_only=False).distance
            all_distances.append((i, distance))

        # Сортируем по расстоянию
        all_distances.sort(key=lambda x: x[1])
        
        # самые далекие результаты (для отладки) 
        # all_distances.sort(key=lambda x: x[1], reverse=True)
        
        # случайные результаты (для отладки) 
        # random.shuffle(all_distances)

        # Шаг 2: Фильтруем близкие индексы
        distinct_results: list[Distance] = []
        for index, dist in all_distances:
            # Проверяем, нет ли уже близкой даты в результатах
            is_close = False
            for existing in distinct_results:
                if abs(index - self.history.index.get_loc(existing.date)) < min_gap:
                    is_close = True
                    break

            # Если не близкий, добавляем
            if not is_close and len(distinct_results) < top_n:
                distinct_results.append(
                    Distance(date=self.history.index[index], distance=dist)
                )

        return distinct_results

    def find_distinct_patterns_sliding(self, top_n: int = 5) -> list[Distance]:
        """
        Находит top_n паттернов через sliding window с победителем.

        Args:
            top_n: количество паттернов для поиска.

        Returns:
            Список Distance с датой и расстоянием.
        """
        pattern = self.reference_pattern.values
        history_values = self.history['close'].tolist()
        pattern_length = len(pattern)

        # Окна начинаются с шагом = pattern_length
        windows: list[Distance] = []
        for window_start in range(0, len(history_values) - pattern_length + 1, pattern_length):
            window_end = window_start + pattern_length

            if window_end > len(history_values):
                break

            # Находим лучший паттерн в этом окне
            best_index = None
            best_distance = float('inf')

            for i in range(window_start, min(window_end, len(history_values) - pattern_length + 1)):
                subsequence = history_values[i:i + pattern_length]
                
                # Нормализуем подпоследовательность через returns-based normalization
                normalized_subsequence = self.normalizer.normalize(subsequence)
                
                distance = compute_dtw(pattern, normalized_subsequence).distance

                if distance < best_distance:
                    best_distance = distance
                    best_index = i

            if best_index is not None:
                windows.append(
                    Distance(date=self.history.index[best_index], distance=best_distance)
                )

        # Сортируем и возвращаем top_n
        windows.sort(key=lambda x: x.distance)
        return windows[:top_n]
