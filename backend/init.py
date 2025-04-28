# Инициализация пакета backend: загружаем переменные окружения из .env, если файл существует.
import os
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
except ImportError:
    # Если python-dotenv не установлен, пропускаем загрузку .env
    pass
