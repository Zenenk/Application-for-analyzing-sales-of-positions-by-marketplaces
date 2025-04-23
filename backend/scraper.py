import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from loguru import logger
from promo_detector import PromoDetector

def init_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--incognito")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver

def scrape_ozon(url, driver):
    driver.get(url)
    time.sleep(3)  # ожидание загрузки
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    products = []
    for card in soup.find_all('div', class_='product-card'):
        name_tag = card.find('a', class_='product-card__title')
        price_tag = card.find('span', class_='product-card__price')
        image_tag = card.find('img')
        if name_tag and price_tag and image_tag:
            product = {
                'name': name_tag.get_text(strip=True),
                'price': float(price_tag.get_text(strip=True).replace('₽', '').replace(' ', '')),
                'image_url': image_tag.get('src'),
                'marketplace': 'Ozon'
            }
            # Применение промо-анализа (OCR+ML)
            detector = PromoDetector()
            product['promotion'] = detector.predict_promotion(product['image_url'])
            products.append(product)
    logger.info(f"Найдено товаров на Ozon: {len(products)}")
    return products

def scrape_wb(url, driver):
    driver.get(url)
    time.sleep(3)  # ожидание загрузки
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    products = []
    for card in soup.find_all('div', class_='product-card'):
        name_tag = card.find('a', class_='product-card__title')
        price_tag = card.find('ins', class_='lower-price')
        image_tag = card.find('img')
        if name_tag and price_tag and image_tag:
            product = {
                'name': name_tag.get_text(strip=True),
                'price': float(price_tag.get_text(strip=True).replace('₽', '').replace(' ', '')),
                'image_url': image_tag.get('src'),
                'marketplace': 'Wildberries'
            }
            detector = PromoDetector()
            product['promotion'] = detector.predict_promotion(product['image_url'])
            products.append(product)
    logger.info(f"Найдено товаров на Wildberries: {len(products)}")
    return products

def scrape_marketplace(config):
    driver = init_driver()
    all_products = []
    for entry in config.get('items', []):
        url = entry.get('identifier')
        if 'ozon' in url.lower():
            products = scrape_ozon(url, driver)
        elif 'wildberries' in url.lower():
            products = scrape_wb(url, driver)
        else:
            # Для Yandex.Market или других площадок – базовая реализация
            products = []
        all_products.extend(products)
    driver.quit()
    return all_products
