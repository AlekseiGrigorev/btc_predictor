"""
Скрипт вычисления DTW-дистанции между первыми и последними 30 записями.
"""

from app.services.predictors.dtw import DTWPredictor


def main():
    print("📊 Вычисление DTW-дистанции...")
    try:
        predictor = DTWPredictor()
        sequence = predictor.predict()

        print(f"✅ DTW-дистанция вычислена успешно.")
        print(f"📅 Диапазон дат: {sequence.date_start.date()} — {sequence.date_end.date()}")
        print(f"📈 Количество значений: {len(sequence.values)}")
        print(f"🔢 Первые 5 значений: {sequence.values[:5]}")
    except ValueError as e:
        print(f"❌ {e}")
    except Exception as e:
        print(f"❌ Непредвиденная ошибка: {e}")


if __name__ == "__main__":
    main()