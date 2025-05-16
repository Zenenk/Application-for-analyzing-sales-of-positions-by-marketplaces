"""
Модели базы данных (определения таблиц) для SQLAlchemy.
"""
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name               = Column(String, nullable=False)
    article            = Column(String, nullable=False)
    price              = Column(String, nullable=False)
    quantity           = Column(String, nullable=False)
    image_url          = Column(String, nullable=True)

    # Новые поля
    promotion_detected = Column(Boolean, default=False, nullable=False)
    detected_keywords  = Column(String, nullable=True)     # ключевые слова через ';'
    parsed_at          = Column(DateTime(timezone=True), nullable=True)

    # Время вставки записи (если parsed_at не передан, можно ориентироваться на timestamp)
    timestamp          = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return (
            f"<Product("
            f"name='{self.name}', "
            f"article='{self.article}', "
            f"price='{self.price}', "
            f"quantity='{self.quantity}', "
            f"image_url='{self.image_url}', "
            f"promotion_detected={self.promotion_detected}, "
            f"detected_keywords='{self.detected_keywords}', "
            f"parsed_at='{self.parsed_at}', "
            f"timestamp='{self.timestamp}'"
            f")>"
        )
