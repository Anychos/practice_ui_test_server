import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # URL вашего API сервера
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8080')

    # Секретный ключ для Flask сессий
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Настройки сессии
    SESSION_TYPE = 'filesystem'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 час
