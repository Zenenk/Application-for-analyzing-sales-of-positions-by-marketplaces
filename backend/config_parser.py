"""Utility to parse configuration from environment or files."""
import os
from dotenv import load_dotenv

# Загружаем .env файл, если он существует
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

def get_token():
    """Возвращает токен API из переменной окружения."""
    return os.getenv("API_TOKEN")

def get_database_path():
    """Возвращает путь к файлу базы данных (SQLite) из переменной окружения или значение по умолчанию."""
    return os.getenv("DATABASE_PATH", "data.sqlite")
