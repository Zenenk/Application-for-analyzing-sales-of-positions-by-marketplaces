# backend/models.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    article = Column(String, nullable=False)
    price = Column(String, nullable=False)
    quantity = Column(String, nullable=False)
    image_url = Column(String, nullable=True)

    promotion_detected = Column(Boolean, default=False)
    detected_keywords = Column(String, nullable=True)

    # Поля для категории и маркетплейса
    marketplace = Column(String, nullable=True)
    category    = Column(String, nullable=True)

    # Поля для хранения данных скидок и промо-лейблов
    price_old    = Column(String, nullable=True)
    price_new    = Column(String, nullable=True)
    discount     = Column(String, nullable=True)
    promo_labels = Column(String, nullable=True)

    parsed_at = Column(DateTime(timezone=True), nullable=True)
    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    def __repr__(self):
        return (
            f"<Product(id={self.id!r}, name={self.name!r}, article={self.article!r}, "
            f"price={self.price!r}, quantity={self.quantity!r})>"
        )
