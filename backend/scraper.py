"""
Модуль для сбора данных с веб-страниц маркетплейсов.
Использует Selenium (headless Chrome) с автоматическим управлением драйвером через webdriver-manager и BeautifulSoup для парсинга HTML.
"""
import time
import shutil
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# Настройка логирования
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def init_driver() -> webdriver.Chrome:
    """
    Инициализирует headless Chrome WebDriver с подходящей версией ChromeDriver.
    Автоматически скачивает драйвер нужной версии через webdriver-manager.
    """
    chrome_options = Options()
    # Указываем бинарник браузера, если установлен через apt-get (chromium)
    chrome_path = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if chrome_path:
        chrome_options.binary_location = chrome_path
    # Запуск в headless-режиме
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # Отключаем логи из браузера
    chrome_options.add_argument("--log-level=3")

    # Сервис с автоматическим управлением драйвером
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver


def scrape_marketplace(
    url: str,
    category_filter: list[str] | None = None,
    article_filter: list[str] | None = None,
    wait: float = 3.0,
    save_html: str | None = None,
) -> list[dict]:
    """
    Собирает данные о продуктах с указанного URL маркетплейса.

    Args:
        url: URL страницы поиска или категории.
        category_filter: список ключевых слов для фильтрации по названию товара.
        article_filter: список ключевых слов для фильтрации по артикулу.
        wait: время ожидания загрузки динамического контента (секунды).
        save_html: путь для сохранения дампа HTML (если указан).

    Returns:
        Список словарей с ключами: name, article, price, quantity, image_url.
    """
    driver = init_driver()
    products: list[dict] = []
    try:
        logger.info(f"Loading page: {url}")
        driver.get(url)
        time.sleep(wait)
        html = driver.page_source

        if save_html:
            Path(save_html).write_text(html, encoding="utf-8")
            logger.info(f"HTML saved to: {save_html}")

        soup = BeautifulSoup(html, "html.parser")

        # TODO: Настроить селекторы под OZON и Wildberries на основе полученных дампов
        product_cards = soup.find_all("div", class_="product-card")
        for card in product_cards:
            name_tag = card.find("h2", class_="product-name")
            name = name_tag.text.strip() if name_tag else ""
            article = card.get("data-article", "")
            price_tag = card.find("span", class_="product-price")
            price = price_tag.text.strip() if price_tag else ""
            quantity_tag = card.find("span", class_="product-quantity")
            quantity = quantity_tag.text.strip() if quantity_tag else ""
            img_tag = card.find("img", class_="product-image")
            image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

            # Фильтрация
            if category_filter and not any(cat.lower() in name.lower() for cat in category_filter):
                continue
            if article_filter and not any(art.lower() in article.lower() for art in article_filter):
                continue

            products.append({
                "name": name,
                "article": article,
                "price": price,
                "quantity": quantity,
                "image_url": image_url,
            })
    except Exception as e:
        logger.error(f"Ошибка при сборе данных: {e}")
    finally:
        driver.quit()

    return products


if __name__ == "__main__":
    # Пример использования (задать реальный URL и фильтры)
    example_url = "https://www.ozon.ru/search/?from_global=true&text=хлебцы"
    results = scrape_marketplace(
        example_url,
        category_filter=["хлебцы"],
        article_filter=None,
        wait=5.0,
        save_html="ozon_dump.html",
    )
    for product in results:
        print(product)
