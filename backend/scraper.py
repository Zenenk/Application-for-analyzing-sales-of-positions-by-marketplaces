"""
Модуль для сбора данных  с веб-страниц маркетплейсов.
Использует Selenium (headless Chrome) для загрузки страниц и BeautifulSoup для парсинга HTML.
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

def init_driver():
    """Инициализирует headless Chrome WebDriver для Selenium."""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_marketplace(url, category_filter=None, article_filter=None):
    """
    Собирает данные о продуктах с страницы маркетплейса по заданному URL.
    Аргументы:
      - url: URL страницы категории маркетплейса.
      - category_filter: список строк (категорий/слов), товары без которых будут отфильтрованы по имени.
      - article_filter: список строк (артикулов или их частей), для фильтрации по артикулу.
    Возвращает список словарей с данными товаров:
      {
        "name": "...",
        "article": "...",
        "price": "...",
        "quantity": "...",
        "image_url": "..."
      }
    """
    driver = init_driver()
    driver.get(url)
    # Ждём некоторое время для загрузки динамического контента
    time.sleep(3)
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    products = []
    product_cards = soup.find_all("div", class_="product-card")
    for card in product_cards:
        name = card.find("h2", class_="product-name")
        name = name.text.strip() if name else "Нет названия"
        article = card.get("data-article", "Нет артикула")
        price_tag = card.find("span", class_="product-price")
        price = price_tag.text.strip() if price_tag else "0"
        quantity_tag = card.find("span", class_="product-quantity")
        quantity = quantity_tag.text.strip() if quantity_tag else "0"
        img_tag = card.find("img", class_="product-image")
        image_url = img_tag["src"] if img_tag else ""
        # Применяем фильтры, если заданы
        if category_filter and not any(cat.lower() in name.lower() for cat in category_filter):
            continue
        if article_filter and not any(art.lower() in article.lower() for art in article_filter):
            continue
        products.append({
            "name": name,
            "article": article,
            "price": price,
            "quantity": quantity,
            "image_url": image_url
        })
    driver.quit()
    return products

# Пример использования скрейпера
if __name__ == "__main__":
    example_url = "https://www.ozon.ru/category/produkty"
    scraped_products = scrape_marketplace(example_url, category_filter=["хлебцы"], article_filter=["гречневые"])
    for prod in scraped_products:
        print(prod)
