from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "sqlite:///marketplace.db"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    article = Column(String, nullable=False)
    price = Column(String, nullable=False)
    quantity = Column(String, nullable=False)
    image_url = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def add_product(product_data):
    """
    Добавляет запись о продукте в базу данных.
    
    product_data: словарь с ключами name, article, price, quantity, image_url.
    """
    session = SessionLocal()
    product = Product(**product_data)
    session.add(product)
    session.commit()
    session.refresh(product)
    session.close()
    return product

def get_products():
    """
    Возвращает список всех продуктов из базы.
    """
    session = SessionLocal()
    products = session.query(Product).all()
    session.close()
    return products

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
