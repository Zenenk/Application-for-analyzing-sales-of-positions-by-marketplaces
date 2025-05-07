import pytest
from backend.database import init_db, add_product, get_products, engine
from backend.models import Base

@pytest.fixture(autouse=True)
def prepare_db():
    # Перед каждым тестом создаём таблицы и после убираем
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)

def test_get_products_empty():
    """Без добавления продуктов get_products() возвращает пустой список."""
    assert get_products() == []

def test_add_and_get_single_product():
    """После add_product() один продукт появляется в get_products()."""
    sample = {
        "name": "P1",
        "article": "A1",
        "price": "10",
        "quantity": "1",
        "image_url": ""
    }
    prod = add_product(sample)
    assert prod.id is not None
    prods = get_products()
    assert len(prods) == 1
    assert prods[0].name == "P1"
    assert prods[0].article == "A1"