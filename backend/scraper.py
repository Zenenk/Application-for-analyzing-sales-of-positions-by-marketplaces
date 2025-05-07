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
    Инициализирует headless Chrome WebDriver с автоматическим управлением драйвером
    через webdriver-manager и базовыми stealth-настройками.
    """
    chrome_options = Options()
    # Указываем бинарник, если установлен chromium
    chrome_path = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if chrome_path:
        chrome_options.binary_location = chrome_path

    chrome_options.add_argument("--headless=new")  # headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    # Stealth options
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    # Hide webdriver property
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument", {
            "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        }
    )
    return driver


def fetch_wb_search(query: str, limit: int = 10) -> List[Dict]:
    """
    Использует публичный JSON-API Wildberries для поиска товаров по тексту.
    Возвращает первые `limit` товаров.
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
            'article': item.get('id'),
            'price': item.get('salePriceU') / 100 if item.get('salePriceU') else None,
            'quantity': item.get('stocks', {}).get('present'),
            'image_url': item.get('image'),
        })
    return products


def fetch_ozon_search(text: str, limit: int = 10) -> List[Dict]:
    """
    Публичный Search API Ozon (composer-api) для поиска по тексту.
    Возвращает первые `limit` товаров.
    """
    api_url = "https://www.ozon.ru/api/composer-api.bx/api/v2/search/searchByText"
    payload = {
        'text': text,
        'page': 1,
        'page_size': limit,
    }
    headers = {
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    resp = requests.post(api_url, json=payload, headers=headers)
    resp.raise_for_status()
    items = resp.json().get('result', {}).get('items', [])
    products = []
    for it in items:
        products.append({
            'name': it.get('title'),
            'article': it.get('id'),
            'price': it.get('price', {}).get('value'),
            'quantity': it.get('stocks', {}).get('quantity'),
            'image_url': it.get('images', [None])[0],
        })
    return products


def fetch_ozon_product(url: str) -> Optional[Dict]:
    """
    Получает данные конкретного товара Ozon через public JSON API.
    URL должен содержать ID товара в конце.
    """
    m = re.search(r"-(\d+)/?$", url)
    if not m:
        logger.error(f"Не удалось извлечь ID из URL: {url}")
        return None
    prod_id = m.group(1)
    api_url = f"https://www.ozon.ru/api/composer-api.bx/api/v2/product/get"
    payload = {'product_id': int(prod_id)}
    headers = {
        'User-Agent': USER_AGENT,
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }
    resp = requests.post(api_url, json=payload, headers=headers)
    resp.raise_for_status()
    item = resp.json().get('result', {})
    return {
        'name': item.get('title'),
        'article': item.get('id'),
        'price': item.get('price', {}).get('value'),
        'quantity': item.get('stocks', {}).get('quantity'),
        'image_url': item.get('images', [None])[0],
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
    Универсальный метод для разбора OZON и Wildberries.
    Для OZON: если URL содержит '/product/', вернет один товар через JSON API,
    иначе выполнит поиск по тексту.
    Для Wildberries: всегда выполнит JSON-поиск.
    """
    if 'ozon.ru/product' in url:
        logger.info(f"🔎 Ozon product page: {url}")
        prod = fetch_ozon_product(url)
        return [prod] if prod else []
    elif 'ozon.ru/search' in url:
        # извлекаем текст запроса
        q = re.search(r'text=([^&]+)', url)
        query = requests.utils.unquote(q.group(1)) if q else ''
        logger.info(f"🔎 Ozon search by text: {query}")
        return fetch_ozon_search(query, limit)
    elif 'wildberries.ru' in url:
        # извлекаем текст запроса
        q = re.search(r'search=([^&]+)', url)
        query = requests.utils.unquote(q.group(1)) if q else ''
        logger.info(f"🔎 Wildberries search: {query}")
        return fetch_wb_search(query, limit)
    else:
        # fallback: Selenium dump + BeautifulSoup
        driver = init_driver()
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
            products = []
            for card in cards[:limit]:
                name = card.find("h2").get_text(strip=True)
                art = card.get("data-article", "")
                price = card.find("span", class_="price").get_text(strip=True)
                qty = card.find("span", class_="quantity").get_text(strip=True)
                img = card.find("img")
                img_url = img["src"] if img and img.has_attr("src") else ""
                if category_filter and not any(cf.lower() in name.lower() for cf in category_filter):
                    continue
                if article_filter and not any(af.lower() in art.lower() for af in article_filter):
                    continue
                products.append({
                    'name': name,
                    'article': art,
                    'price': price,
                    'quantity': qty,
                    'image_url': img_url,
                })
            return products
        finally:
            driver.quit()


if __name__ == "__main__":
    # Пример: конкретный товар на OZON
    print(scrape_marketplace(
        "https://www.ozon.ru/product/hlebtsy-grechnevye-bez-soli-i-glyutena-tm-prodpostavka-15-sht-po-60-g-postnye-1636757719/",
        category_filter=["хлебцы"]
    ))
    # Пример: первые 10 товаров на Wildberries
    print(scrape_marketplace(
        "https://www.wildberries.ru/catalog/0/search.aspx?search=хлебцы",
        category_filter=["хлебцы"]
    ))
