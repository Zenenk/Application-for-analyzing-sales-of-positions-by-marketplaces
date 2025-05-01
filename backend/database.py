"""
Модуль для работы с базой данных (инициализация, функции добавления/получения данных).
Используется PostgreSQL (URL подключения задаётся через переменную окружения DATABASE_URL).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend import models
from loguru import logger

# Получаем URL базы данных из переменной окружения
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL не указана")

# Создаем движок SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)
# Создаем фабрику сессий
SessionLocal = sessionmaker(bind=engine)
# Получаем базовый класс моделей и класс модели Product из модуля models
Base = models.Base
Product = models.Product

def init_db():
    """Создает все таблицы в базе данных (если они ещё не созданы)."""
    Base.metadata.create_all(bind=engine)

def add_product(product_data):
    """
    Добавляет информацию о продукте в базу данных.
    product_data: словарь с ключами name, article, price, quantity, image_url.
    Возвращает объект Product, добавленный в базу.
    """
    session = SessionLocal()
    try:
        product = Product(**product_data)
        session.add(product)
        session.commit()
        session.refresh(product)
        logger_message = (f"Добавлен продукт в БД: {product.name} (арт. {product.article})")
        print(logger_message)
        return product
    finally:
        session.close()

def get_products():
    """Возвращает список всех продуктов (объекты Product) из базы данных."""
    session = SessionLocal()
    try:
        products = session.query(Product).all()
        return products
    finally:
        session.close()


# Если запускать модуль напрямую, выполним простой тест вставки
if __name__ == "__main__":
    init_db()
    sample_product = {
        "name": "Хлебцы гречневые",
        "article": "ART123",
        "price": "100 руб.",
        "quantity": "20",
        "image_url": "http://example.com/image1.jpg"
    }
    added = add_product(sample_product)
    print("Добавлен продукт:", added.name)
