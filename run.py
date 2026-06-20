import uvicorn
from app.main import app
from app.db import init_db

if __name__ == "__main__":
    print("🚀 Инициализация базы данных SQLite...")
    try:
        init_db()
        print("✅ База данных успешно инициализирована (файл data/stocks.db).")
    except Exception as e:
        print(f"❌ Ошибка при инициализации БД: {e}")
        exit(1)

    print("🌐 Запуск веб-сервера...")
    print("📍 Откройте в браузере: http://localhost:8000")
    print("📍 API документация (Swagger): http://localhost:8000/docs")
    
    # Запускаем сервер Uvicorn
    uvicorn.run(
        app,                # экземпляр нашего FastAPI приложения
        host="127.0.0.1",   # слушаем только localhost (безопасно для локальной разработки)
        port=8000#,          # порт по умолчанию
        #reload=True         # автоматическая перезагрузка при изменении кода (удобно для разработки)
    )
