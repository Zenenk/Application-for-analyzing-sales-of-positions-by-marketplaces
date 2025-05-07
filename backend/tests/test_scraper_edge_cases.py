import pytest
from backend.scraper import scrape_marketplace

def make_driver(html):
    class D:
        page_source = html
        def get(self, url): pass
        def quit(self): pass
    return D()

@pytest.mark.parametrize("category_filter,article_filter,expected", [
    (None, None, 1),     # без фильтров — возвращаем всё
    (["foo"], [], 0),    # фильтр по категории не проходит
])
def test_scrape_without_filters(monkeypatch, category_filter, article_filter, expected):
    html = """
    <div class="product-card" data-article="A1">
      <h2 class="product-name">Name</h2>
      <span class="product-price">5</span>
      <span class="product-quantity">3</span>
      <img class="product-image" src="u"/>
    </div>
    """
    monkeypatch.setattr("backend.scraper.init_driver", lambda: make_driver(html))
    prods = scrape_marketplace("url", category_filter=category_filter, article_filter=article_filter)
    assert len(prods) == expected

def test_scrape_missing_tags_produces_defaults(monkeypatch):
    html = '<div class="product-card"></div>'
    monkeypatch.setattr("backend.scraper.init_driver", lambda: make_driver(html))
    prods = scrape_marketplace("url", None, None)
    assert len(prods) == 1
    p = prods[0]
    assert p["name"] == "Нет названия"
    assert p["article"] == "Нет артикула"
    assert p["price"] == "0"
    assert p["quantity"] == "0"
    assert p["image_url"] == ""