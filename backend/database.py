import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from backend.models import Base, Product

# Получение URL базы данных из переменных окружения
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("Environment variable DATABASE_URL must be set")

# Создание SQLAlchemy Engine для PostgreSQL
engine = create_engine(DATABASE_URL)

# Фабрика сессий
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Инициализация базы данных: создание таблиц
def init_db():
    Base.metadata.create_all(bind=engine)

# Добавление нового продукта в базу данных
# product_data должен содержать ключи:
# name, article, price, quantity, image_url,
# promotion_detected, detected_keywords,
# price_old, price_new, discount, promo_labels,
# parsed_at (строка ISO или datetime)
def add_product(product_data: dict) -> Product:
    session = SessionLocal()
    try:
        # Обработка parsed_at
        parsed_at = None
        if product_data.get("parsed_at"):
            val = product_data["parsed_at"]
            parsed_at = (
                val if isinstance(val, datetime)
                else datetime.fromisoformat(val)
            )

        prod = Product(
            name=product_data.get("name", ""),
            article=product_data.get("article", ""),
            price=product_data.get("price", 0),
            quantity=product_data.get("quantity", 0),
            image_url=product_data.get("image_url"),

            promotion_detected=product_data.get("promotion_detected", False),
            detected_keywords=product_data.get("detected_keywords", ""),

            price_old=product_data.get("price_old"),
            price_new=product_data.get("price_new"),
            discount=product_data.get("discount"),
            promo_labels=product_data.get("promo_labels"),

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

# Получение всех продуктов из базы данных
def get_products():
    session = SessionLocal()
    try:
        return session.query(Product).all()
    finally:
        session.close()

# Получение истории продукта по артикулу
# Возвращает список словарей, отсортированных по parsed_at по возрастанию
def get_product_history(article: str):
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

# Удаление старых данных из базы
# Удаляет записи старше, чем сейчас минус days дней
# Возвращает количество удаленных записей
def clean_old_data(days: int = 60) -> int:
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
