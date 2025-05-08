import os
import re
import time
import random
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Optional

import configparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def read_config(config_file: str) -> dict:
    """
    Reads and parses the configuration file into a nested dict by section.

    Args:
        config_file: Path to the config file.

    Returns:
        A dict where each key is a section name and value is a dict of options to their raw string values.
    """
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    cp = configparser.ConfigParser()
    cp.read(config_file, encoding='utf-8')

    result = {}
    for section in cp.sections():
        # preserve raw string values
        items = dict(cp.items(section))
        result[section] = items
    return result


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -----------------------
# Настройка прокси/UA
# -----------------------
# Переменная окружения SCRAPER_PROXIES: строка вида "http://ip1:port,http://ip2:port"
PROXY_LIST = [p.strip() for p in os.getenv("SCRAPER_PROXIES", "").split(",") if p.strip()]
# Статичный список User-Agent’ов
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
]

def get_random_user_agent() -> str:
    return random.choice(UA_LIST)

def get_random_proxy() -> Optional[Dict[str, str]]:
    if not PROXY_LIST:
        return None
    p = random.choice(PROXY_LIST)
    return {"http": p, "https": p}

def get_session() -> requests.Session:
    """
    Сессия с Retry-логикой и рандомным UA + опциональным прокси.
    """
    session = requests.Session()
    retries = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    session.headers.update({"User-Agent": get_random_user_agent()})
    proxy = get_random_proxy()
    if proxy:
        session.proxies.update(proxy)
        logger.info(f"Using proxy: {proxy['http']}")

    return session

# -----------------------
# Selenium-driver
# -----------------------
def init_driver() -> webdriver.Chrome:
    """
    Инициализирует headless Chrome WebDriver с автоматическим управлением драйвером
    и базовыми stealth-настройками.
    """
    chrome_options = Options()
    # указываем бинарник chromium, если есть
    chrome_path = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if chrome_path:
        chrome_options.binary_location = chrome_path

    chrome_options.add_argument(f"--user-agent={get_random_user_agent()}")
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # скрываем webdriver
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"}
    )
    return driver


def fetch_wb_search(query: str, limit: int = 10) -> List[Dict]:
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
    session = get_session()
    try:
        resp = session.get(url, params=params, timeout=10)
    except requests.RequestException as e:
        logger.error(f"WB API failed: {e}")
        return []
    if resp.status_code != 200:
        logger.error(f"WB API HTTP {resp.status_code} for '{query}'")
        return []

    try:
        data = resp.json().get('data', {})
    except ValueError as e:
        logger.error(f"WB JSON decode error: {e}")
        return []

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
    api_url = "https://www.ozon.ru/api/composer-api.bx/api/v2/search/searchByText"
    params = {
        'text': text,
        'page': 1,
        'page_size': limit,
    }
    session = get_session()
    try:
        resp = session.get(api_url, params=params, timeout=10)
    except requests.RequestException as e:
        logger.error(f"Ozon search API failed: {e}")
        return []
    if resp.status_code != 200:
        logger.error(f"Ozon API HTTP {resp.status_code} for '{text}'")
        return []

    try:
        data = resp.json()
    except ValueError as e:
        logger.error(f"Ozon JSON decode error: {e}")
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
    m = re.search(r"-(\d+)/?$", url)
    if not m:
        logger.error(f"Cannot extract product ID from URL: {url}")
        return None
    prod_id = m.group(1)
    api_url = "https://www.ozon.ru/api/composer-api.bx/api/v2/product/get"
    payload = {'product_id': int(prod_id)}
    session = get_session()
    try:
        resp = session.post(api_url, json=payload, timeout=10)
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
    Если URL содержит "/product/" → fetch_ozon_product
    elif "ozon.ru/search" → fetch_ozon_search
    elif "wildberries.ru" → fetch_wb_search
    else → Selenium + BeautifulSoup fallback.
    """
    # 1) Ozon: конкретный товар
    if "/ozon.ru/product/" in url:
        logger.info(f"🔎 Ozon product page: {url}")
        prod = fetch_ozon_product(url)
        return [prod] if prod else []

    # 2) Ozon: поиск
    if "ozon.ru/search" in url:
        q = re.search(r"text=([^&]+)", url)
        query = requests.utils.unquote(q.group(1)) if q else ""
        logger.info(f"🔎 Ozon search by text: {query}")
        return fetch_ozon_search(query, limit)

    # 3) Wildberries
    if "wildberries.ru" in url:
        q = re.search(r"search=([^&]+)", url)
        query = requests.utils.unquote(q.group(1)) if q else ""
        logger.info(f"🔎 Wildberries search: {query}")
        return fetch_wb_search(query, limit)

    # 4) Fallback: Selenium + BS
    driver = init_driver()
    products: List[Dict] = []
    try:
        logger.info(f"Loading page via Selenium: {url}")
        driver.get(url)
        time.sleep(wait)
        html = driver.page_source
        if save_html:
            Path(save_html).write_text(html, encoding="utf-8")
            logger.info(f"HTML dumped to {save_html}")

        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("div", class_="product-card")
        for card in cards[:limit]:
            # дефолты
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
            if article_filter and not any(af.lower() in article.lower() for af in (article_filter or [])):
                continue

            products.append({
                "name": name,
                "article": article,
                "price": price,
                "quantity": quantity,
                "image_url": image_url,
            })
    except Exception as e:
        logger.error(f"Ошибка fallback-парсинга: {e}")
    finally:
        driver.quit()

    return products

if __name__ == "__main__":
    print(scrape_marketplace(
        "https://www.ozon.ru/product/hlebtsy-grechnevye-bez-soli-i-glyutena-tm-prodpostavka-15-sht-po-60-g-postnye-1636757719/",
        category_filter=["хлебцы"]
    ))
    print(scrape_marketplace(
        "https://www.wildberries.ru/catalog/0/search.aspx?search=хлебцы",
        category_filter=["хлебцы"]
    ))
