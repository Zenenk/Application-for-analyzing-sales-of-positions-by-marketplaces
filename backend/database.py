# backend/database.py

"""
Модуль для работы с базой данных (инициализация, функции добавления/получения данных).
Поддерживает два режима:
  - При запуске через pytest — in-memory SQLite.
  - Во всех остальных случаях — по DATABASE_URL из окружения (или SQLite по умолчанию).
"""

import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from loguru import logger

# Выбираем URL БД: при тестах — память, иначе — из окружения
if any('pytest' in arg for arg in sys.argv):
    DATABASE_URL = "sqlite:///:memory:"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

# Создаём движок и сессии SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

Base = models.Base
Product = models.Product

def init_db():
    """
    Создаёт все таблицы в базе данных (если они ещё не созданы).
    """
    Base.metadata.create_all(bind=engine)

def add_product(product_data):
    """
    Добавляет информацию о продукте в базу данных.
    
    Args:
      product_data: dict с ключами name, article, price, quantity, image_url.
      
    Returns:
      Экземпляр Product, добавленный в БД.
    """
    session = SessionLocal()
    try:
        product = Product(**product_data)
        session.add(product)
        session.commit()
        session.refresh(product)
        logger.info(f"Добавлен продукт в БД: {product.name} (арт. {product.article})")
        return product
    finally:
        session.close()

def get_products():
    """
    Возвращает список всех продуктов из базы данных.
    
    Returns:
      List[Product]
    """
    session = SessionLocal()
    try:
        return session.query(Product).all()
    finally:
        session.close()

# Тестовый запуск
if __name__ == "__main__":
    init_db()
    sample_product = {
        "name": "Тестовый продукт",
        "article": "TEST001",
        "price": "50 руб.",
        "quantity": "10",
        "image_url": "http://example.com/test.jpg"
    }
    added = add_product(sample_product)
    print("Добавлен продукт:", added.name)
