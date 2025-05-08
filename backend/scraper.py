import time
import shutil
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# User-Agent for HTTP requests
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
)


def init_driver() -> webdriver.Chrome:
    """
    Инициализирует headless Chrome WebDriver с автозагрузкой драйвера
    через webdriver-manager и лёгкими stealth-опциями.
    """
    chrome_options = Options()
    # Попытка найти системный Chrome/Chromium
    chrome_path = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if chrome_path:
        chrome_options.binary_location = chrome_path

    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # Stealth
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # Скрыть webdriver-флаг
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        }
    )
    return driver


def fetch_wb_search(query: str, limit: int = 10) -> List[Dict]:
    """
    Публичный JSON-API Wildberries: поиск по тексту.
    """
    url = "https://search.wb.ru/exactmatch/ru/common/v4/search"
    params = {
        'appType': 1,
        'couponsGeo': '12,3,1',
        'curr': 'rub',
        'dest': '-1257786,-1257779,-1257773',
        'emp': 0,
        'locale': 'ru',
        'pricemarginCoeff': 1.0,
        'page': 1,
        'query': query,
    }
    headers = {'User-Agent': USER_AGENT}
    resp = requests.get(url, params=params, headers=headers)
    resp.raise_for_status()
    data = resp.json().get('data', {})
    products = []
    for item in data.get('products', [])[:limit]:
        products.append({
            'name': item.get('name'),
            'article': str(item.get('id', '')),
            'price': (item.get('salePriceU') or 0) / 100,
            'quantity': item.get('stocks', {}).get('present'),
            'image_url': item.get('image'),
        })
    return products


def fetch_ozon_search(text: str, limit: int = 10) -> List[Dict]:
    """
    Публичный Search API Ozon: поиск по тексту.
    """
    api_url = "https://www.ozon.ru/api/composer-api.bx/api/v2/search/searchByText"
    params = {
        'text': text,
        'page': 1,
        'page_size': limit,
    }
    headers = {
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    try:
        resp = requests.get(api_url, params=params, headers=headers, timeout=10)
    except requests.RequestException as e:
        logger.error(f"Ozon API request failed: {e}")
        return []

    if resp.status_code != 200:
        logger.error(f"Ozon API returned HTTP {resp.status_code} for text '{text}'")
        return []

    try:
        data = resp.json()
    except ValueError as e:
        logger.error(f"Failed to decode JSON from Ozon API: {e}")
        return []

    items = data.get('result', {}).get('items', [])
    products = []
    for it in items:
        products.append({
            'name': it.get('title'),
            'article': str(it.get('id', '')),
            'price': it.get('price', {}).get('value'),
            'quantity': it.get('stocks', {}).get('quantity'),
            'image_url': (it.get('images') or [None])[0],
        })
    return products


def fetch_ozon_product(url: str) -> Optional[Dict]:
    """
    Данные одного товара Ozon через JSON API.
    URL должен заканчиваться на -<id>/
    """
    m = re.search(r"-(\d+)/?$", url)
    if not m:
        logger.error(f"Не удалось извлечь ID из URL: {url}")
        return None
    prod_id = m.group(1)
    api_url = "https://www.ozon.ru/api/composer-api.bx/api/v2/product/get"
    payload = {'product_id': int(prod_id)}
    headers = {
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    try:
        resp = requests.post(api_url, json=payload, headers=headers, timeout=10)
    except requests.RequestException as e:
        logger.error(f"Ozon product API failed: {e}")
        return None

    if resp.status_code != 200:
        logger.error(f"Ozon product API HTTP {resp.status_code} for ID {prod_id}")
        return None

    try:
        item = resp.json().get('result', {})
    except ValueError as e:
        logger.error(f"Ozon product JSON decode error: {e}")
        return None

    return {
        'name': item.get('title'),
        'article': str(item.get('id', '')),
        'price': item.get('price', {}).get('value'),
        'quantity': item.get('stocks', {}).get('quantity'),
        'image_url': (item.get('images') or [None])[0],
    }


def scrape_marketplace(
    url: str,
    category_filter: Optional[List[str]] = None,
    article_filter: Optional[List[str]] = None,
    limit: int = 10,
    wait: float = 3.0,
    save_html: Optional[str] = None,
) -> List[Dict]:
    """
    Универсальный парсер: OZON (search/product), Wildberries и fallback.
    """
    # 1) OZON: конкретный товар
    if 'ozon.ru/product' in url:
        logger.info(f"🔎 Ozon product page: {url}")
        prod = fetch_ozon_product(url)
        return [prod] if prod else []

    # 2) OZON: поиск по тексту
    if 'ozon.ru/search' in url:
        q = re.search(r'text=([^&]+)', url)
        query = requests.utils.unquote(q.group(1)) if q else ''
        logger.info(f"🔎 Ozon search by text: {query}")
        return fetch_ozon_search(query, limit)

    # 3) Wildberries: JSON API
    if 'wildberries.ru' in url:
        q = re.search(r'search=([^&]+)', url)
        query = requests.utils.unquote(q.group(1)) if q else ''
        logger.info(f"🔎 Wildberries search: {query}")
        return fetch_wb_search(query, limit)

    # 4) Fallback: Selenium + BeautifulSoup
    driver = init_driver()
    products: List[Dict] = []
    try:
        logger.info(f"Loading page via Selenium: {url}")
        driver.get(url)
        time.sleep(wait)
        html = driver.page_source
        if save_html:
            Path(save_html).write_text(html, encoding="utf-8")
            logger.info(f"HTML saved to: {save_html}")

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("div", class_="product-card")
        for card in cards[:limit]:
            name_tag = card.find("h2", class_="product-name")
            name = name_tag.get_text(strip=True) if name_tag else "Нет названия"

            article = card.get("data-article", "Нет артикула")

            price_tag = card.find("span", class_="product-price")
            price = price_tag.get_text(strip=True) if price_tag else "0"

            qty_tag = card.find("span", class_="product-quantity")
            quantity = qty_tag.get_text(strip=True) if qty_tag else "0"

            img_tag = card.find("img", class_="product-image")
            image_url = img_tag["src"] if img_tag and img_tag.has_attr("src") else ""

            # фильтрация
            if category_filter and not any(cf.lower() in name.lower() for cf in category_filter):
                continue
            if article_filter and not any(af.lower() in article.lower() for af in article_filter):
                continue

            products.append({
                "name": name,
                "article": article,
                "price": price,
                "quantity": quantity,
                "image_url": image_url,
            })
    except Exception as e:
        logger.error(f"Ошибка при fallback-парсинге: {e}")
    finally:
        driver.quit()

    return products


if __name__ == "__main__":
    # Тестовые примеры
    print(scrape_marketplace(
        "https://www.ozon.ru/product/hlebtsy-grechnevye-bez-soli-i-glyutena-tm-prodpostavka-15-sht-po-60-g-postnye-1636757719/",
        category_filter=["хлебцы"]
    ))
    print(scrape_marketplace(
        "https://www.wildberries.ru/catalog/0/search.aspx?search=хлебцы",
        category_filter=["хлебцы"]
    ))

