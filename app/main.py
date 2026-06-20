from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pathlib import Path

from app.services.dtw_pattern_finder import DTWPatternFinder
from app.services.normalizers import CumulativeSumReturnNormalizer, CumulativeReturnNormalizer
from app.services.storage import TimeframeStorage
from app.services import Transformer, QuotesManager

# Определяем базовую директорию проекта (на уровень выше app/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Словарь для преобразования кодов таймфреймов в человекочитаемые названия
TIMEFRAME_LABELS = {
    "1d": "дневной (1 день)",
    "4h": "4-часовой (4 часа)",
    "1h": "часовой (1 час)",
}

# Создаем экземпляр приложения
app = FastAPI(
    title="Stock Predictor API",
    description="Локальное приложение для прогноза котировок",
    version="1.0.0"
)

# 1. Подключаем раздачу статических файлов (CSS, JS)
# Теперь файлы из папки static/ будут доступны по пути /static/...
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# 2. Настраиваем движок шаблонов (для отдачи index.html)
templates = Jinja2Templates(directory=BASE_DIR / "templates")


# -----------------------------------------------------------------------------
# Веб-маршруты (отдача страниц)
# -----------------------------------------------------------------------------

@app.get("/")
def home(request: Request):
    """Отдает главную HTML-страницу"""
    return templates.TemplateResponse(request=request, name="index.html")


# -----------------------------------------------------------------------------
# API-маршруты (для общения с фронтендом через fetch)
# -----------------------------------------------------------------------------

@app.post("/api/load_data")
async def load_data(payload: dict):
    """
    Эндпоинт для кнопки 'Загрузить данные'.

    Тело запроса может содержать поле 'timeframe' (по умолчанию '1d').
    """
    timeframe = payload.get("timeframe", "1d")
    manager = QuotesManager(timeframe=timeframe)
    count = manager.update_quotes()
    return {
        "status": "success",
        "message": f"[{timeframe}] Данные ({count} записей) успешно загружены в БД"
    }


@app.get("/api/chart_data")
async def get_chart_data(
    top_n: int = Query(5, description="Количество похожих паттернов"),
    days: int = Query(30, description="Длина паттерна (количество свечей)"),
    timeframe: str = Query("1d", description="Таймфрейм: 1d, 4h, 1h"),
):
    """
    Эндпоинт для кнопки 'Построить график'.

    Args:
        top_n: Количество наиболее похожих паттернов для поиска.
        days: Длина эталонного паттерна (количество свечей).
        timeframe: Таймфрейм данных ('1d', '4h', '1h').
    """
    # Загружаем все исторические данные из БД для указанного таймфрейма
    storage = TimeframeStorage(timeframe)
    history_df = storage.get_all_records()

    # Проверяем, что данных достаточно для поиска паттернов
    if history_df.empty or len(history_df) < days * 2:
        return {"patterns": []}

    normalizer = CumulativeReturnNormalizer()

    # Инициализируем поисковик паттернов
    finder = DTWPatternFinder(
        history=history_df,
        pattern_length=days,
        normalizer=normalizer,
    )

    # Если эталонный паттерн не создан (недостаточно данных)
    if finder.reference_pattern is None:
        return {"patterns": []}

    # Ищем top_n наиболее похожих паттернов
    patterns = finder.find_distinct_patterns_filtered(top_n=top_n, min_gap=days)

    # Получаем эталонный паттерн (последние days значений) через Transformer
    reference_seq = Transformer.transform_last_to_sequence(history_df, days)
    reference_values = {
        "label": reference_seq.date_start.strftime('%Y-%m-%d %H:%M'),
        "data": normalizer.normalize(reference_seq.values),
    }

    # Формируем ответ для фронтенда
    result_patterns = []
    for pattern in patterns:
        # Получаем индекс начала паттерна в истории
        pattern_start_idx = history_df.index.get_loc(pattern.date)

        # Извлекаем pattern_length * 2 цен из истории, начиная с даты паттерна
        pattern_prices = (
            history_df['close']
            .iloc[pattern_start_idx:pattern_start_idx + days * 2]
            .tolist()
        )

        # Нормализуем цены через процентные доходности
        normalized_prices = normalizer.normalize(pattern_prices)

        # Форматируем дату и время для label
        label = pattern.date.strftime('%Y-%m-%d %H:%M')

        result_patterns.append({
            "label": label,
            "data": normalized_prices,
        })

    return {
        "prompt": (
            f"Ты — профессиональный крипто-аналитик и количественный исследователь. "
            f"Твоя задача — спрогнозировать динамику цены биткоина на основе технического анализа предоставленных данных.\n\n"
            f"### ВВОДНЫЕ ДАННЫЕ ###\n"
            f"Данные представлены в виде объекта JSON у которого есть поля prompt (текущий промпт), patterns и reference\n"
            f"Поле 'prompt' в JSON — это инструкция для тебя, не анализируй его как данные. "
            f"Данные для анализа находятся в корневых полях этого же JSON-объекта: patterns и reference. Используй их для прогноза."
            f"Анализируй только поля 'patterns' и 'reference'.\n"
            f"Таймфрейм данных data: {TIMEFRAME_LABELS.get(timeframe, timeframe)}\n"
            f"Поле reference: массив относительного изменения цены биткоина за последние {days} свечей (текущая рыночная ситуация).\n"
            f"Поле patterns: массив объектов, каждый из которых содержит label и data. data представляет набор исторических данных, наиболее похожих на reference (найдены по алгоритму DTW). "
            f"Каждый паттерн (поле data) состоит из двух частей: \n"
            f"   - Первая половина ({days} значений): историческое движение, похожее на reference.\n"
            f"   - Вторая половина ({days} значений): то, как цена вела себя после этого в прошлом (используем для прогноза).\n"
            f"Поле label: дата начала каждого исторического паттерна (для привязки к макро-контексту того времени).\n\n"
              
            f"### ЗАДАЧА ###\n"
            f"1. Проанализируй первую и вторую половину исторических паттернов (data) с учетом таймфрейма {TIMEFRAME_LABELS.get(timeframe, timeframe)}: к чему они приводили в прошлом?\n"
            f"2. Сопоставь исторический опыт с текущим reference с учетом таймфрейма {TIMEFRAME_LABELS.get(timeframe, timeframe)}.\n"
            f"3. Спрогнозируй изменение цены биткоина на следующие {days} свечей в процентах от текущей цены с учетом таймфрейма {TIMEFRAME_LABELS.get(timeframe, timeframe)}.\n\n"
        ),
        "patterns": result_patterns,
        "reference": reference_values,
    }
    
    return {
        "prompt": (
            f"Ты — профессиональный крипто-аналитик и количественный исследователь. "
            f"Твоя задача — спрогнозировать динамику цены биткоина на основе исторических паттернов и макро-контекста.\n\n"
            f"### ВВОДНЫЕ ДАННЫЕ ###\n"
            f"Данные представлены в виде объекта JSON у которого есть поля prompt (текущий промпт), patterns и reference\n"
            f"Поле 'prompt' в JSON — это инструкция для тебя, не анализируй его как данные. "
            f"Данные для анализа находятся в корневых полях этого же JSON-объекта: patterns и reference. Используй их для прогноза."
            f"Анализируй только поля 'patterns' и 'reference'.\n"
            f"Таймфрейм данных data: {TIMEFRAME_LABELS.get(timeframe, timeframe)}\n"
            f"Поле reference: массив относительного изменения цены биткоина за последние {days} свечей (текущая рыночная ситуация).\n"
            f"Поле patterns: массив объектов, каждый из которых содержит label и data. data представляет набор исторических данных, наиболее похожих на reference (найдены по алгоритму DTW). "
            f"Каждый паттерн (поле data) состоит из двух частей: \n"
            f"   - Первая половина ({days} значений): историческое движение, похожее на reference.\n"
            f"   - Вторая половина ({days} значений): то, как цена вела себя после этого в прошлом (используем для прогноза).\n"
            f"Поле label: дата начала каждого исторического паттерна (для привязки к макро-контексту того времени).\n\n"
            
            f"### МАКРО-КОНТЕКСТ И НОВОСТИ ###\n"
            f"Если ты можешь искать в сети интернет, то загрузи актуальные новости, макро-показатели и актуальный фон которые влияют на цену биткоина.\n"
            
            f"### ЗАДАЧА ###\n"
            f"1. Проанализируй вторую половину исторических паттернов (data) с учетом таймфрейма {TIMEFRAME_LABELS.get(timeframe, timeframe)}: к чему они приводили в прошлом?\n"
            f"2. Сопоставь исторический опыт с текущим новостным фоном и макро-показателями с учетом таймфрейма {TIMEFRAME_LABELS.get(timeframe, timeframe)}.\n"
            f"3. Спрогнозируй изменение цены биткоина на следующие {days} свечей в процентах от текущей цены с учетом таймфрейма {TIMEFRAME_LABELS.get(timeframe, timeframe)}.\n\n"
        ),
        "patterns": result_patterns,
        "reference": reference_values,
    }