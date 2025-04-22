import unittest
from unittest.mock import patch
from backend.scraper import scrape_marketplace

# Класс-заменитель драйвера для тестирования
class DummyDriver:
    def __init__(self, html):
        self.html = html
    def get(self, url):
        pass
    @property
    def page_source(self):
        return self.html
    def quit(self):
        pass

# Пример HTML для теста
dummy_html = """
<html>
<body>
<div class="product-card" data-article="ART123">
    <h2 class="product-name">Хлебцы гречневые</h2>
    <span class="product-price">100 руб.</span>
    <span class="product-quantity">20</span>
    <img class="product-image" src="http://example.com/image1.jpg" />
</div>
<div class="product-card" data-article="ART456">
    <h2 class="product-name">Продукт без категории</h2>
    <span class="product-price">200 руб.</span>
    <span class="product-quantity">15</span>
    <img class="product-image" src="http://example.com/image2.jpg" />
</div>
</body>
</html>
"""

class TestScraper(unittest.TestCase):
    @patch('app.scraper.init_driver')
    def test_scrape_marketplace(self, mock_init_driver):
        mock_driver = DummyDriver(dummy_html)
        mock_init_driver.return_value = mock_driver
        
        products = scrape_marketplace("http://dummy-url", category_filter=["Хлебцы"], article_filter=["ART123"])
        self.assertEqual(len(products), 1)
        product = products[0]
        self.assertEqual(product["name"], "Хлебцы гречневые")
        self.assertEqual(product["article"], "ART123")
        self.assertEqual(product["price"], "100 руб.")
        self.assertEqual(product["quantity"], "20")
        self.assertEqual(product["image_url"], "http://example.com/image1.jpg")

if __name__ == "__main__":
    unittest.main()
