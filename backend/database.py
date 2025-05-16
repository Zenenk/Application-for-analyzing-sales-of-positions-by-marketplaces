# backend/database.py

import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models
from loguru import logger

# Выбираем URL БД: при тестах — память, иначе — из окружения
if any('pytest' in arg for arg in sys.argv):
    DATABASE_URL = "sqlite:///:memory:"
else:
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///:memory:")

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)

Base    = models.Base
Product = models.Product

def init_db():
    """
    Создаёт все таблицы в базе данных (если они ещё не созданы).
    """
    Base.metadata.create_all(bind=engine)

def add_product(product_data: dict):
    """
    Добавляет информацию о продукте в базу данных.
    
    Args:
      product_data: dict с ключами:
        - name (str)
        - article (str)
        - price (str or float)
        - quantity (str or int)
        - image_url (str, optional)
        - promotion_detected (bool, optional)
        - detected_keywords (str, optional) — ключевые слова через ';'
        - parsed_at (datetime, optional)
    Returns:
      Экземпляр Product, добавленный в БД.
    """
    session = SessionLocal()
    try:
        # Если parsed_at передали строкой, пытаемся преобразовать
        if "parsed_at" in product_data and isinstance(product_data["parsed_at"], str):
            try:
                product_data["parsed_at"] = datetime.fromisoformat(product_data["parsed_at"])
            except ValueError:
                # некорректный формат — выбрасываем
                raise ValueError(f"parsed_at имеет неверный ISO-формат: {product_data['parsed_at']}")
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

if __name__ == "__main__":
    init_db()
    # пример
    sample = {
        "name":               "Тест",
        "article":            "TEST001",
        "price":              "100",
        "quantity":           "5",
        "image_url":          "",
        "promotion_detected": True,
        "detected_keywords":  "скидка;акция",
        "parsed_at":          "2025-05-12T12:00:00"
    }
    added = add_product(sample)
    print("Добавлен продукт:", added)
