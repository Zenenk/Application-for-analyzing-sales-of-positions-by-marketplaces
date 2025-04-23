import pytest
from scraper import scrape_ozon
from selenium.webdriver.chrome.webdriver import WebDriver

class DummyDriver:
    def __init__(self, html):
        self._html = html
    def get(self, url):
        pass
    @property
    def page_source(self):
        return self._html
    def quit(self):
        pass

def test_scrape_ozon():
    # Пример HTML для теста (упрощённый)
    html = """
    <html><body>
    <div class="product-card">
      <a class="product-card__title">Товар Тест 1</a>
      <span class="product-card__price">1 000 ₽</span>
      <img src="http://example.com/image1.jpg"/>
    </div>
    </body></html>
    """
    driver = DummyDriver(html)
    products = scrape_ozon("http://ozon.ru/test", driver)
    assert len(products) == 1
    assert products[0]['name'] == "Товар Тест 1"
