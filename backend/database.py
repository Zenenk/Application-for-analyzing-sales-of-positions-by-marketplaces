# backend/database.py


from datetime import datetime, timedelta
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from backend.models import Base, Product
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def add_product(product_data: dict) -> Product:
    """
    product_data должен содержать ключи:
    name, article, price, quantity, image_url,
    promotion_detected, detected_keywords,
    price_old, price_new, discount, promo_labels,
    parsed_at (строка ISO или datetime)
    """
    session = SessionLocal()
    try:
        # Обработка parsed_at
        parsed_at = None
        if "parsed_at" in product_data and product_data["parsed_at"]:
            from datetime import datetime
            val = product_data["parsed_at"]
            parsed_at = (
                val if isinstance(val, datetime)
                else datetime.fromisoformat(val)
            )

        prod = Product(
            name=product_data.get("name", ""),
            article=product_data.get("article", ""),
            price=product_data.get("price", ""),
            quantity=product_data.get("quantity", ""),
            image_url=product_data.get("image_url", None),

            promotion_detected=product_data.get("promotion_detected", False),
            detected_keywords=product_data.get("detected_keywords", ""),

            # === Новые поля ===
            price_old=product_data.get("price_old", None),
            price_new=product_data.get("price_new", None),
            discount=product_data.get("discount", None),
            promo_labels=product_data.get("promo_labels", None),

            parsed_at=parsed_at
        )
        session.add(prod)
        session.commit()
        session.refresh(prod)
        return prod
    except SQLAlchemyError:
        session.rollback()
        raise
    finally:
        session.close()

def get_products():
    session = SessionLocal()
    try:
        return session.query(Product).all()
    finally:
        session.close()

def get_product_history(article: str):
    """
    Возвращает список словарей с историей по артикулу,
    отсортированных по parsed_at по возрастанию.
    """
    session = SessionLocal()
    try:
        rows = (
            session.query(Product)
            .filter(Product.article == article)
            .order_by(asc(Product.parsed_at))
            .all()
        )
        history = []
        for p in rows:
            history.append({
                "parsed_at": p.parsed_at.isoformat() if p.parsed_at else None,
                "price": p.price,
                "price_old": p.price_old,
                "price_new": p.price_new,
                "discount": p.discount,
                "quantity": p.quantity,
            })
        return history
    finally:
        session.close()

def clean_old_data(days: int = 60) -> int:
    """
    Удаляет все записи из таблицы products,
    у которых timestamp ранее, чем сейчас минус days.
    Возвращает число удалённых записей.
    """
    cutoff = datetime.utcnow() - timedelta(days=days)
    session = SessionLocal()
    try:
        deleted = (
            session.query(Product)
            .filter(Product.timestamp < cutoff)
            .delete(synchronize_session=False)
        )
        session.commit()
        return deleted
    finally:
        session.close()
