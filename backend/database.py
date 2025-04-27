"""Database interaction module for storing products and their history."""
from datetime import datetime
from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

Base = declarative_base()
_engine = None
_Session = None

def init_db(db_path: str):
    """Initialize the SQLite database and create tables if not exist."""
    global _engine, _Session
    _engine = create_engine(f"sqlite:///{db_path}")
    _Session = sessionmaker(bind=_engine)
    # Определение моделей
    class Product(Base):
        __tablename__ = "products"
        id = Column(Integer, primary_key=True, autoincrement=True)
        marketplace = Column(String)
        url = Column(String, unique=True)
        title = Column(String)
        price = Column(Float)
        stock = Column(Integer, nullable=True)
        in_promo = Column(Boolean, default=False)
        # Связь с историей
        history = relationship("History", back_populates="product", cascade="all, delete-orphan")

        def to_dict(self):
            return {
                "id": self.id,
                "marketplace": self.marketplace,
                "url": self.url,
                "title": self.title,
                "price": self.price,
                "stock": self.stock,
                "in_promo": self.in_promo
            }

    class History(Base):
        __tablename__ = "history"
        id = Column(Integer, primary_key=True)
        product_id = Column(Integer, ForeignKey("products.id"))
        timestamp = Column(DateTime, default=datetime.utcnow)
        price = Column(Float)
        stock = Column(Integer, nullable=True)
        in_promo = Column(Boolean)
        product = relationship("Product", back_populates="history")

        def to_dict(self):
            return {
                "timestamp": self.timestamp.isoformat(),
                "price": self.price,
                "stock": self.stock,
                "in_promo": self.in_promo
            }

    # Сохраняем модели в модуль, чтобы использовать в других функциях
    globals()["Product"] = Product
    globals()["History"] = History
    # Создаём таблицы
    Base.metadata.create_all(_engine)

def _get_session():
    if _Session is None:
        raise RuntimeError("Database not initialized. Call init_db first.")
    return _Session()

def add_product(product_data: dict):
    """Добавляет новый товар и его начальную историю в базу. Возвращает объект Product."""
    session = _get_session()
    Product = globals()["Product"]
    History = globals()["History"]
    # Создаем запись продукта
    product = Product(
        marketplace=product_data["marketplace"],
        url=product_data["url"],
        title=product_data["title"],
        price=product_data["price"],
        stock=product_data.get("stock"),
        in_promo=product_data.get("in_promo", False)
    )
    session.add(product)
    session.commit()
    # Создаем первую запись истории для этого товара
    history_entry = History(
        product_id=product.id,
        price=product.price,
        stock=product.stock,
        in_promo=product.in_promo
    )
    session.add(history_entry)
    session.commit()
    session.refresh(product)  # обновляем объект product с учётом связанной истории
    session.close()
    return product

def update_product(product: object, new_data: dict):
    """Обновляет данные товара (цена, остаток, промо) и добавляет новую запись в историю."""
    session = _get_session()
    Product = globals()["Product"]
    History = globals()["History"]
    # Обновляем поля продукта
    product.price = new_data.get("price", product.price)
    product.stock = new_data.get("stock", product.stock)
    product.in_promo = new_data.get("in_promo", product.in_promo)
    session.add(product)
    # Добавляем запись в историю
    history_entry = History(
        product_id=product.id,
        price=product.price,
        stock=product.stock,
        in_promo=product.in_promo
    )
    session.add(history_entry)
    session.commit()
    session.close()
    return product

def get_all_products() -> List[object]:
    """Возвращает список всех товаров (Product) из базы."""
    session = _get_session()
    products = session.query(globals()["Product"]).all()
    session.close()
    return products

def get_history(product_id: int) -> List[object]:
    """Возвращает список всех записей истории (History) для данного товара."""
    session = _get_session()
    Product = globals()["Product"]
    History = globals()["History"]
    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        session.close()
        return None
    # Получаем историю, отсортированную по времени
    history = session.query(History).filter(History.product_id == product_id).order_by(History.timestamp).all()
    session.close()
    return history

def delete_product(product_id: int) -> bool:
    """Удаляет товар и связанные с ним данные. Возвращает True, если товар существовал и был удалён."""
    session = _get_session()
    Product = globals()["Product"]
    product = session.query(Product).filter(Product.id == product_id).first()
    if not product:
        session.close()
        return False
    session.delete(product)
    session.commit()
    session.close()
    return True
