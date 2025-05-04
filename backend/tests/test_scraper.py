import unittest
from unittest.mock import patch
from scraper import scrape_marketplace

# Класс-заглушка для имитации Selenium WebDriver
class DummyDriver:
    def __init__(self, html):
        self.page_source = html
    def get(self, url):
        # Ничего не делаем, HTML уже задан
        pass
    def quit(self):
        pass

# Пример HTML для теста скрейпера (два продукта, один подходит под фильтры)
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
    @patch('backend.scraper.init_driver')
    def test_scrape_marketplace(self, mock_init_driver):
        # Подменяем init_driver, чтобы вернуть DummyDriver с подготовленным HTML вместо реального браузера
        mock_driver = DummyDriver(dummy_html)
        mock_init_driver.return_value = mock_driver
        products = scrape_marketplace("http://dummy-url", category_filter=["хлебцы"], article_filter=["ART123"])
        # Ожидаем, что после фильтрации останется только один продукт
        self.assertEqual(len(products), 1)
        product = products[0]
        # Проверяем поля продукта
        self.assertEqual(product["name"], "Хлебцы гречневые")
        self.assertEqual(product["article"], "ART123")
        self.assertEqual(product["price"], "100 руб.")
        self.assertEqual(product["quantity"], "20")
        self.assertEqual(product["image_url"], "http://example.com/image1.jpg")

if __name__ == "__main__":
    unittest.main()
