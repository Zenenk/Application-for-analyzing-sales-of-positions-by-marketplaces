# scraper.py
import logging
from datetime import datetime
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs, unquote

from bs4 import BeautifulSoup
from backend.config_parser import make_session, get_ozon_session, _init_uc, human_delay

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def fetch_ozon_search(text: str, limit: int = 10, referer: Optional[str] = None) -> List[Dict]:
    api = "https://www.ozon.ru/api/composer-api.bx/api/v2/search/searchByText"
    params = {"text": text, "page": 1, "page_size": limit, "__rr": 1}
    session = get_ozon_session()
    session.headers.update({"Accept": "application/json, text/plain, */*", "X-Requested-With": "XMLHttpRequest"})
    if referer:
        session.headers["Referer"] = referer
    r = session.get(api, params=params, timeout=15)
    r.raise_for_status()
    items = r.json().get("result", {}).get("items", [])
    products = []
    for it in items[:limit]:
        products.append({
            "name": it.get("title", ""),
            "article": str(it.get("id", "")),
            "price": it.get("price", {}).get("value", 0),
            "quantity": it.get("stocks", {}).get("quantity", 0),
            "image_url": (it.get("images") or [None])[0] or "",
            "parsed_at": datetime.utcnow()
        })
    return products


def fetch_ozon_product(url: str) -> Optional[Dict]:
    import re
    m = re.search(r"-(\d+)/?$", url)
    if not m:
        return None
    pid = m.group(1)
    api = "https://www.ozon.ru/api/composer-api.bx/api/v2/product/get"
    payload = {"product_id": int(pid)}
    session = get_ozon_session()
    session.headers.update({"Accept": "application/json, text/plain, */*", "X-Requested-With": "XMLHttpRequest", "Referer": url})
    r = session.post(api, json=payload, timeout=15)
    r.raise_for_status()
    item = r.json().get("result", {})
    return {
        "name": item.get("title", ""),
        "article": str(item.get("id", "")),
        "price": item.get("price", {}).get("value", 0),
        "quantity": item.get("stocks", {}).get("quantity", 0),
        "image_url": (item.get("images") or [None])[0] or "",
        "parsed_at": datetime.utcnow()
    }


def fetch_wb_search(query: str, limit: int = 10) -> List[Dict]:
    session = make_session()
    session.headers.update({"Accept": "application/json, text/plain, */*", "Referer": "https://www.wildberries.ru/"})
    api_url = f"https://search.wb.ru/exactmatch/ru/common/v4/search?query={query}&page=1&limit={limit}"
    r = session.get(api_url, timeout=15)
    r.raise_for_status()
    data = r.json().get("data", [])
    products = []
    for item in data[:limit]:
        detail = fetch_wb_product(str(item.get("id", "")))
        if detail:
            products.append(detail)
    return products


def fetch_wb_product(article: str) -> Optional[Dict]:
    session = make_session()
    session.headers.update({"Accept": "application/json, text/plain, */*", "Referer": "https://www.wildberries.ru/"})
    api_url = f"https://card.wb.ru/cards/detail?appType=1&curr=rub&dest=-1257786&nm={article}"
    r = session.get(api_url, timeout=15)
    r.raise_for_status()
    products_data = r.json().get("data", {}).get("products", [])
    if not products_data:
        return None
    p = products_data[0]
    price = p.get("salePriceU") or p.get("priceU") or 0
    return {
        "name": p.get("name", ""),
        "article": str(p.get("id", "")),
        "price": price / 100,
        "quantity": p.get("stocks", {}).get("qty", 0),
        "image_url": (p.get("images") or [{}])[0].get("url", ""),
        "parsed_at": datetime.utcnow()
    }


def fallback_scrape_with_uc(
    url: str,
    limit: int = 10,
    category_filter: Optional[List[str]] = None,
    article_filter: Optional[List[str]] = None
) -> List[Dict]:
    driver = _init_uc()
    driver.get(url)
    human_delay()
    html = driver.page_source
    driver.quit()
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div[data-widget='searchResultsV2'] a")[:limit]
    products = []
    for card in cards:
        name = card.select_one("h4").get_text(strip=True) if card.select_one("h4") else ""
        link = card.get("href", "")
        article = link.rstrip("/").split("-")[-1]
        price = card.select_one("div[data-test-id='tile-price']").get_text(strip=True) if card.select_one("div[data-test-id='tile-price']") else ""
        img = card.select_one("img")
        img_url = img["src"] if img and img.has_attr("src") else ""
        parsed = datetime.utcnow()
        prod = {"name": name, "article": article, "price": price, "quantity": "", "image_url": img_url, "parsed_at": parsed}
        if category_filter and not any(cf.lower() in name.lower() for cf in category_filter):
            continue
        if article_filter and not any(af.lower() in article.lower() for af in article_filter):
            continue
        products.append(prod)
    return products


def scrape_marketplace(
    url: str,
    category_filter: Optional[List[str]] = None,
    article_filter: Optional[List[str]] = None,
    limit: int = 10
) -> List[Dict]:
    if "ozon.ru/product" in url:
        prod = fetch_ozon_product(url)
        return [prod] if prod else []
    if "ozon.ru/search" in url or "ozon.ru/category" in url:
        if "search" in url:
            query = unquote(parse_qs(urlparse(url).query).get("text", [""])[0])
        else:
            slug = urlparse(url).path.rstrip("/").split("/")[-1]
            query = slug.rsplit("-", 1)[0].replace("-", " ")
        results = fetch_ozon_search(query, limit, referer=url)
        return results if results else fallback_scrape_with_uc(url, limit, category_filter, article_filter)
    if "wildberries.ru" in url:
        query = unquote(parse_qs(urlparse(url).query).get("search", [""])[0])
        results = fetch_wb_search(query, limit)
        return results if results else fallback_scrape_with_uc(url, limit, category_filter, article_filter)
    return fallback_scrape_with_uc(url, limit, category_filter, article_filter)
