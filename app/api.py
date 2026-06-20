from pybit.v5 import V5

# Создание клиента
session = V5(
    testnet=False,  # False для боевой среды, True для тестнета
    api_key="YOUR_API_KEY",  # Можно оставить пустым для публичных API
    api_secret="YOUR_API_SECRET"
)

# Получение свечей (kline)
response = session.get_kline(
    symbol="BTCUSDT",
    interval="15",  # 15 минут
    limit=100  # количество свечей
)

# Извлечение данных в формате списка
candles = response['result']['list']
# candles = [[timestamp, open, high, low, close, volume, ...], ...]

# Преобразование в список цен закрытия (close prices)
close_prices = [float(candle[4]) for candle in candles]


from pybit.v5 import V5

session = V5(testnet=False)  # Только публичные API, ключи не нужны

# Получить 500 свечей BTCUSDT на 15-минутном таймфрейме
response = session.get_kline(
    symbol="BTCUSDT",
    interval="15",
    limit=500
)

close_prices = [float(candle[4]) for candle in response['result']['list']]



from pybit.v5 import V5
from datetime import datetime

# Создание клиента
session = V5(testnet=False)

# Временные интервалы (в формате timestamp в миллисекундах)
start_time = int(datetime(2026, 6, 1, 0, 0).timestamp() * 1000)  # 1 июня 2026
end_time = int(datetime(2026, 6, 10, 0, 0).timestamp() * 1000)  # 10 июня 2026

# Получение свечей за период
response = session.get_kline(
    symbol="BTCUSDT",
    interval="15",  # 15 минут
    start=start_time,  # Начало периода (timestamp в мс)
    end=end_time,  # Конец периода (timestamp в мс)
    limit=1000  # Максимум свечей в запросе (Bybit лимит 1500)
)

close_prices = [float(candle[4]) for candle in response['result']['list']]



def fetch_klines_paged(symbol="BTCUSDT", interval="15", start_time=None, end_time=None):
    """
    Получает свечи за период с пагинацией (если > 1500 свечей)
    """
    from pybit.v5 import V5
    
    if start_time is None:
        start_time = int(datetime(2026, 1, 1).timestamp() * 1000)
    if end_time is None:
        end_time = int(datetime.now().timestamp() * 1000)
    
    session = V5(testnet=False)
    data = []
    
    current_end = end_time
    
    while current_end > start_time:
        response = session.get_kline(
            symbol=symbol,
            interval=interval,
            start=start_time,
            end=current_end,
            limit=1000
        )
        
        candles = response['result']['list']
        if not candles:
            break
        
        data.extend(candles)
        current_end = candles[0][0] - 1  # timestamp предыдущей свечи
        
        time.sleep(0.2)  # Избегаем rate limits
    
    return data
    
    
    
# Старая версия pybit
client = bybit(test=True, api_key="...", api_secret="...")
x = client.LinearKline.LinearKline_get(
    symbol="BTCUSDT",
    interval="5",
    **{'from': 1581231260}  # timestamp в секундах
).result()