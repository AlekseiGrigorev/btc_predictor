"""
Скрипт для тестирования всех методов поиска паттернов в DTWPatternFinder.
Каждый метод запускается и выводит результаты в консоль.
"""

from app.services.dtw_pattern_finder import DTWPatternFinder
from app.services.normalizers.sum_return import CumulativeSumReturnNormalizer


# Параметры поиска
PATTERN_LENGTH: int = 30  # Длина эталонного паттерна (дней)
TOP_N: int = 5            # Количество лучших результатов
MIN_GAP: int = 30         # Минимальный зазор между паттернами
WINDOW: int = 10          # Размер окна для оптимизированного поиска


def print_results(method_name: str, results: list) -> None:
    """
    Выводит результаты поиска в отформатированном виде.

    Args:
        method_name: Название метода.
        results: Список Distance с датой и расстоянием.
    """
    print(f"\n=== {method_name} ===")
    if not results:
        print("  (нет результатов)")
        return
    for i, dist in enumerate(results, start=1):
        print(f"  {i}. Дата: {dist.date.date()}, Расстояние: {dist.distance:.6f}")


def main() -> None:
    """Основная функция: создаёт DTWPatternFinder и запускает все методы поиска."""
    print("📊 Поиск похожих паттернов с использованием DTW (Dynamic Time Warping)...")
    print(f"   Длина паттерна: {PATTERN_LENGTH}")
    print(f"   История загружается из БД...")

    # Загружаем все исторические данные из БД
    from app.services.storage import get_all_records
    history_df = get_all_records()

    # Создаём экземпляр поисковика паттернов с передачей DataFrame
    finder = DTWPatternFinder(history=history_df, pattern_length=PATTERN_LENGTH, normalizer=CumulativeSumReturnNormalizer())

    # Проверяем, что истории достаточно для поиска
    if finder.reference_pattern is None:
        print(f"\n❌ Недостаточно данных в БД: требуется минимум {PATTERN_LENGTH * 2} записей.")
        return

    print(f"   Эталонный паттерн: {finder.reference_pattern.date_start.date()} — "
          f"{finder.reference_pattern.date_end.date()}")
    print(f"   Длина истории для поиска: {len(finder.history)} записей")
    print()

    # 1. find_multiple_patterns — полный перебор
    try:
        results = finder.find_multiple_patterns(top_n=TOP_N)
        print_results("find_multiple_patterns (полный перебор)", results)
    except Exception as e:
        print(f"\n=== find_multiple_patterns ===\n  ❌ Ошибка: {e}")

    # 2. find_patterns_optimized — с фильтрацией кандидатов
    try:
        results = finder.find_patterns_optimized(top_n=TOP_N, window=WINDOW)
        print_results("find_patterns_optimized (с пороговой фильтрацией)", results)
    except Exception as e:
        print(f"\n=== find_patterns_optimized ===\n  ❌ Ошибка: {e}")

    # 3. find_distinct_patterns — с равномерным шагом
    try:
        results = finder.find_distinct_patterns(top_n=TOP_N, min_gap=MIN_GAP)
        print_results("find_distinct_patterns (с равномерным шагом)", results)
    except Exception as e:
        print(f"\n=== find_distinct_patterns ===\n  ❌ Ошибка: {e}")

    # 4. find_distinct_patterns_filtered — полный перебор + пост-фильтрация
    try:
        results = finder.find_distinct_patterns_filtered(top_n=TOP_N, min_gap=MIN_GAP)
        print_results("find_distinct_patterns_filtered (перебор + фильтрация близких)", results)
    except Exception as e:
        print(f"\n=== find_distinct_patterns_filtered ===\n  ❌ Ошибка: {e}")

    # 5. find_distinct_patterns_sliding — скользящее окно
    try:
        results = finder.find_distinct_patterns_sliding(top_n=TOP_N)
        print_results("find_distinct_patterns_sliding (скользящее окно)", results)
    except Exception as e:
        print(f"\n=== find_distinct_patterns_sliding ===\n  ❌ Ошибка: {e}")


if __name__ == "__main__":
    main()