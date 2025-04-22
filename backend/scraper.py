from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def init_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def scrape_marketplace(url, category_filter=None, article_filter=None):
    """
    Получает данные с маркетплейса по заданному URL.
    
    Аргументы:
      - url: URL страницы маркетплейса.
      - category_filter: список категорий для фильтрации товаров (опционально).
      - article_filter: список артикулов для фильтрации товаров (опционально).
      
    Возвращает список словарей с данными товара:
    {
        "name": "Название товара",
        "article": "Артикул",
        "price": "Цена",
        "quantity": "Остаток",
        "image_url": "Ссылка на изображение"
    }
    """
    driver = init_driver()
    driver.get(url)
    time.sleep(3)  # Ждем загрузку страницы
    html = driver.page_source
    soup = BeautifulSoup(html, "html.parser")
    
    # Пример разбора страницы
    products = []
    product_cards = soup.find_all("div", class_="product-card")
    for card in product_cards:
        name = card.find("h2", class_="product-name").text.strip() if card.find("h2", class_="product-name") else "Нет названия"
        article = card.get("data-article", "Нет артикула")
        price = card.find("span", class_="product-price").text.strip() if card.find("span", class_="product-price") else "0"
        quantity = card.find("span", class_="product-quantity").text.strip() if card.find("span", class_="product-quantity") else "0"
        image = card.find("img", class_="product-image")["src"] if card.find("img", class_="product-image") else ""
        
        # Фильтрация (если заданы)
        if category_filter and not any(cat.lower() in name.lower() for cat in category_filter):
            continue
        if article_filter and not any(art.lower() in article.lower() for art in article_filter):
            continue
        
        products.append({
            "name": name,
            "article": article,
            "price": price,
            "quantity": quantity,
            "image_url": image
        })
    
    driver.quit()
    return products

if __name__ == "__main__":
    url = "https://www.ozon.ru/category/produkty"
    products = scrape_marketplace(url, category_filter=["хлебцы"], article_filter=["хлебцы гречневые"])
    print(products)
