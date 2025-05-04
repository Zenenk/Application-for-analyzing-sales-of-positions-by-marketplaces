import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import init_db, Product, Base

class TestDatabase(unittest.TestCase):
    def setUp(self):
        # Инициализируем временную базу SQLite для тестирования
        self.test_engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(bind=self.test_engine)
        self.TestSession = sessionmaker(bind=self.test_engine)

    def test_add_and_get_product(self):
        # Используем сеанс, привязанный к памяти
        session = self.TestSession()
        sample_product = {
            "name": "Тестовый продукт",
            "article": "TEST001",
            "price": "50 руб.",
            "quantity": "10",
            "image_url": "http://example.com/test.jpg"
        }
        # Добавляем продукт через ORM напрямую (проверяем работу модели)
        product = Product(**sample_product)
        session.add(product)
        session.commit()
        # Запрашиваем из базы и проверяем
        products = session.query(Product).all()
        self.assertEqual(len(products), 1)
        self.assertEqual(products[0].name, "Тестовый продукт")
        session.close()

if __name__ == "__main__":
    unittest.main()
