# backend/scraper.py

import os
import random
import time
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs, unquote

from playwright.sync_api import sync_playwright, Browser, Page
from backend.config_parser import get_random_user_agent, get_random_proxy, human_delay

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Проксировать Playwright через тот же список, что и requests
def _get_playwright_proxy():
    p = get_random_proxy()
    if not p:
        return None
    # p - {'http': 'http://ip:port'}
    url = p['http']
    # Playwright ожидает вида "http://ip:port"
    return {"server": url}

def _launch_browser() -> Browser:
    pw = sync_playwright().start()
    proxy = _get_playwright_proxy()
    return pw.chromium.launch(
        headless=True,
        proxy=proxy,
        args=[
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            f"--user-agent={get_random_user_agent()}",
        ]
    )

def _new_page(browser: Browser) -> Page:
    context = browser.new_context(
        viewport={"width": 1280, "height": 800},
        user_agent=get_random_user_agent(),
        java_script_enabled=True,
        ignore_https_errors=True,
    )
    # подставляем Referer, если нужно, будем переписывать перед goto
    return context.new_page()

def scrape_marketplace(
    url: str,
    category_filter: Optional[List[str]] = None,
    article_filter: Optional[List[str]] = None,
    limit: int = 10,
    wait: float = 3.0,
    save_html: Optional[str] = None,
) -> List[Dict]:
    """
    Универсальный парсер с Playwright:
      1) Ozon product
      2) Ozon search/category
      3) Wildberries JSON API
      4) Fallback: JS-render via Playwright + BS
    """
    logger.info(f"🔍 scrape_marketplace URL={url} (dump: {save_html or 'none'})")
    products: List[Dict] = []

    # 1) Ozon product API
    if 'ozon.ru/product' in url:
        from backend.scraper import fetch_ozon_product  # avoid circular
        return [fetch_ozon_product(url)] if fetch_ozon_product(url) else []

    # 2) Ozon search/category via JSON API first
    if 'ozon.ru/search' in url or 'ozon.ru/category' in url:
        # извлекаем текст
        query = ''
        if 'search' in url:
            query = unquote(parse_qs(urlparse(url).query).get('text', [''])[0])
        else:
            # category slug → название
            slug = urlparse(url).path.rstrip('/').split('/')[-1]
            query = slug.rsplit('-', 1)[0].replace('-', ' ')
        from backend.scraper import fetch_ozon_search
        js_res = fetch_ozon_search(query, limit, referer=url)
        if js_res:
            return js_res
        # иначе — рендерим через Playwright
        logger.info("⚠️ Ozon JSON-API empty, falling back to Playwright")
        browser = _launch_browser()
        page = _new_page(browser)
        page.set_extra_http_headers({"Referer": url})
        page.goto(url, wait_until='networkidle')
        human_delay()
        html = page.content()
        if save_html:
            with open(save_html, 'w', encoding='utf-8') as f:
                f.write(html)
        # вытягиваем из DOM первые карточки
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        cards = soup.select('div[data-widget="searchResultsV2"] article div > a')[:limit]
        for a in cards:
            try:
                name = a.select_one('h4') .get_text(strip=True)
                link = a['href']
                article = link.rstrip('/').split('-')[-1]
                price = a.select_one('div[data-test-id="tile-price"]').get_text(strip=True)
                img = a.select_one('img')
                img_url = img['src'] if img and img.has_attr('src') else ''
                products.append({
                    "name": name,
                    "article": article,
                    "price": price,
                    "quantity": "",  # Ozon не показывает остаток в списке
                    "image_url": img_url,
                })
            except Exception:
                continue
        browser.close()
        return products

    # 3) Wildberries JSON API (тот же код что раньше, только через get_random_user_agent + proxy)
    if 'wildberries.ru' in url:
        from backend.scraper import fetch_wb_search
        return fetch_wb_search(unquote(parse_qs(urlparse(url).query).get('search', [''])[0]), limit)

    # 4) Любой другой URL → Fallback Playwright + BS
    browser = _launch_browser()
    page = _new_page(browser)
    page.goto(url, wait_until='networkidle')
    human_delay()
    html = page.content()
    if save_html:
        with open(save_html, 'w', encoding='utf-8') as f:
            f.write(html)
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    cards = soup.select("div.product-card")[:limit]
    for card in cards:
        name = card.select_one("h2.product-name")
        name = name.get_text(strip=True) if name else ""
        article = card.get("data-article", "")
        price = card.select_one("span.product-price")
        price = price.get_text(strip=True) if price else ""
        qty = card.select_one("span.product-quantity")
        qty = qty.get_text(strip=True) if qty else ""
        img = card.select_one("img.product-image")
        img_url = img['src'] if img and img.has_attr('src') else ""
        if category_filter and not any(cf.lower() in name.lower() for cf in category_filter):
            continue
        if article_filter and not any(af.lower() in article.lower() for af in article_filter):
            continue
        products.append({
            "name": name,
            "article": article,
            "price": price,
            "quantity": qty,
            "image_url": img_url,
        })
    browser.close()
    return products


# JSON-API helper functions здесь же или в старом модуле
def fetch_ozon_search(text: str, limit: int = 10, referer: Optional[str] = None) -> List[Dict]:
    from backend.config_parser import get_session
    api = "https://www.ozon.ru/api/composer-api.bx/api/v2/search/searchByText"
    params = {'text': text, 'page': 1, 'page_size': limit, '__rr': 1}
    sess = get_session()
    sess.headers.update({
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
    })
    if referer:
        sess.headers["Referer"] = referer
    try:
        r = sess.get(api, params=params, timeout=10)
        r.raise_for_status()
        data = r.json().get('result', {}).get('items', [])
    except Exception as e:
        logger.error(f"Ozon search API failed: {e}")
        return []
    return [{
        'name': it.get('title'),
        'article': str(it.get('id', '')),
        'price': it.get('price', {}).get('value'),
        'quantity': it.get('stocks', {}).get('quantity'),
        'image_url': (it.get('images') or [None])[0],
    } for it in data]

def fetch_ozon_product(url: str) -> Optional[Dict]:
    import re
    from backend.config_parser import get_session
    m = re.search(r"-(\d+)/?$", url)
    if not m:
        return None
    pid = m.group(1)
    api = "https://www.ozon.ru/api/composer-api.bx/api/v2/product/get"
    payload = {'product_id': int(pid)}
    sess = get_session()
    sess.headers.update({
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": url
    })
    try:
        r = sess.post(api, json=payload, timeout=10)
        r.raise_for_status()
        item = r.json().get('result', {})
    except Exception as e:
        logger.error(f"Ozon product API failed: {e}")
        return None
    return {
        'name': item.get('title'),
        'article': str(item.get('id', '')),
        'price': item.get('price', {}).get('value'),
        'quantity': item.get('stocks', {}).get('quantity'),
        'image_url': (item.get('images') or [None])[0],
    }
