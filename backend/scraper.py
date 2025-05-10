# backend/scraper.py

import os
import random
import time
import logging
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs, unquote

from bs4 import BeautifulSoup
import requests
from requests.exceptions import HTTPError
from playwright.sync_api import sync_playwright, Playwright, BrowserContext
from selenium.common.exceptions import WebDriverException

from backend.config_parser import (
    _rnd_ua,
    _rnd_proxy,
    human_delay,
    init_driver,
    get_ozon_session,
    get_wb_session,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def _get_playwright_proxy() -> Optional[dict]:
    p = _rnd_proxy()
    if not p:
        return None
    return {"server": p["http"]}


def _launch_chrome_persistent() -> BrowserContext:
    """
    Запускает Chromium с постоянным профилем (persistent context),
    чтобы сохранить cookies/localStorage после прохождения JS-челленджа.
    """
    pw: Playwright = sync_playwright().start()

    # создаём временную папку для user data
    profile_dir = Path(tempfile.mkdtemp(prefix="ozon-profile-"))
    # пытаемся скопировать системный Chrome-профиль, чтобы избежать ошибок
    if os.name == "nt":
        src_profile = Path(os.getenv("LOCALAPPDATA", "")) / "Google/Chrome/User Data"
    else:
        src_profile = Path.home() / ".config/google-chrome"
    try:
        shutil.copytree(src_profile, profile_dir, dirs_exist_ok=True)
    except Exception:
        pass

    context: BrowserContext = pw.chromium.launch_persistent_context(
        user_data_dir=str(profile_dir),
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            f"--user-agent={_rnd_ua()}",
        ],
        viewport={"width": 1366, "height": 768},
        locale="ru-RU",
        timezone_id="Europe/Moscow",
        ignore_https_errors=True,
        proxy=_get_playwright_proxy(),
    )
    return context


def _launch_chrome_context() -> BrowserContext:
    """
    Обычный Chromium-контекст (non-persistent), чистая сессия для рендеринга.
    """
    pw: Playwright = sync_playwright().start()
    browser = pw.chromium.launch(
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-setuid-sandbox",
            "--disable-dev-shm-usage",
            f"--user-agent={_rnd_ua()}",
        ],
        proxy=_get_playwright_proxy(),
    )
    context: BrowserContext = browser.new_context(
        viewport={"width": 1366, "height": 768},
        user_agent=_rnd_ua(),
        locale="ru-RU",
        timezone_id="Europe/Moscow",
        ignore_https_errors=True,
    )
    return context


def scrape_marketplace(
    url: str,
    category_filter: Optional[List[str]] = None,
    article_filter: Optional[List[str]] = None,
    limit: int = 10,
    wait: float = 3.0,
    save_html: Optional[str] = None,
) -> List[Dict]:
    """
    Универсальный парсер:
      1) Ozon product → API
      2) Ozon search/category → API + persistent Chromium → BS4
      3) Wildberries search → API
      4) Фоллбек: чистый Chromium → BS4
    """
    logger.info(f"🔍 scrape_marketplace URL={url}")

    # 1) Ozon product page
    if "ozon.ru/product" in url:
        from backend.scraper import fetch_ozon_product
        prod = fetch_ozon_product(url)
        return [prod] if prod else []

    # 2) Ozon search/category
    if "ozon.ru/search" in url or "ozon.ru/category" in url:
        # извлекаем текст запроса
        if "search" in url:
            q = unquote(parse_qs(urlparse(url).query).get("text", [""])[0])
        else:
            slug = urlparse(url).path.rstrip("/").split("/")[-1]
            q = slug.rsplit("-", 1)[0].replace("-", " ")

        # 2.1) Попытка Ozon JSON-API
        try:
            items = fetch_ozon_search(q, limit)
            if items:
                return items
            logger.info("Ozon API вернул пусто, переходим в браузер")
        except HTTPError as e:
            logger.warning(f"Ozon API HTTPError {e}, fallback to browser")

        # 2.2) Persistent Chromium: проходим JS-челлендж, сохраняем cookies
        try:
            ctx = _launch_chrome_persistent()
            page = ctx.new_page()
            page.goto(url, wait_until="networkidle")
            human_delay(wait, wait + 2)
            html = page.content()
            if save_html:
                with open(save_html, "w", encoding="utf-8") as f:
                    f.write(html)
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select('div[data-widget="searchResultsV2"] article')[:limit]
            products = []
            for card in cards:
                try:
                    name = card.select_one("h4").get_text(strip=True)
                    link = card.select_one("a")["href"]
                    article = link.rstrip("/").split("-")[-1]
                    price = card.select_one('div[data-test-id="tile-price"]').get_text(strip=True)
                    img = card.select_one("img")
                    img_url = img["src"] if img and img.has_attr("src") else ""
                    products.append({
                        "name": name,
                        "article": article,
                        "price": price,
                        "quantity": "",
                        "image_url": img_url,
                    })
                except Exception:
                    continue
            ctx.close()
            return products
        except Exception as e:
            logger.error(f"Selenium/Playwright fallback для Ozon failed: {e}")

    # 3) Wildberries search via API
    if "wildberries.ru" in url:
        from backend.scraper import fetch_wb_search
        try:
            txt = unquote(parse_qs(urlparse(url).query).get("search", [""])[0])
            res = fetch_wb_search(txt, limit)
            if res:
                return res
        except Exception as e:
            logger.warning(f"Wildberries API failed: {e}")

    # 4) Generic fallback: чистый Chromium + BS4
    try:
        ctx = _launch_chrome_context()
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle")
        human_delay(wait, wait + 2)
        html = page.content()
        if save_html:
            with open(save_html, "w", encoding="utf-8") as f:
                f.write(html)
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select("div.product-card")[:limit]
        products = []
        for card in cards:
            name_el = card.select_one("h2.product-name")
            name = name_el.get_text(strip=True) if name_el else ""
            article = card.get("data-article", "")
            price_el = card.select_one("span.product-price")
            price = price_el.get_text(strip=True) if price_el else ""
            qty_el = card.select_one("span.product-quantity")
            qty = qty_el.get_text(strip=True) if qty_el else ""
            img = card.select_one("img.product-image")
            img_url = img["src"] if img and img.has_attr("src") else ""
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
        ctx.close()
        return products
    except WebDriverException as e:
        logger.error(f"Generic Chromium fallback failed: {e}")
        return []


# --- JSON-API helpers ---

def fetch_ozon_search(text: str, limit: int = 10) -> List[Dict]:
    """
    Fetch Ozon search results via API.
    Raises HTTPError on 4xx/5xx.
    """
    api = "https://www.ozon.ru/api/composer-api.bx/api/v2/search/searchByText"
    params = {"text": text, "page": 1, "page_size": limit, "__rr": 2}
    sess = get_ozon_session()
    sess.headers.update({
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.ozon.ru/search/?text={text}"
    })
    r = sess.get(api, params=params, timeout=15)
    r.raise_for_status()
    data = r.json().get("result", {}).get("items", [])
    return [
        {
            "name": it.get("title"),
            "article": str(it.get("id", "")),
            "price": it.get("price", {}).get("value"),
            "quantity": it.get("stocks", {}).get("quantity"),
            "image_url": (it.get("images") or [None])[0],
        }
        for it in data
    ]


def fetch_ozon_product(url: str) -> Optional[Dict]:
    """
    Fetch single Ozon product via API.
    """
    import re
    m = re.search(r"-(\d+)/?$", url)
    if not m:
        return None
    pid = int(m.group(1))
    api = "https://www.ozon.ru/api/composer-api.bx/api/v2/product/get"
    sess = get_ozon_session()
    sess.headers.update({
        "Accept": "application/json, text/plain, */*",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": url
    })
    r = sess.post(api, json={"product_id": pid}, timeout=15)
    try:
        r.raise_for_status()
    except Exception:
        return None
    item = r.json().get("result", {})
    return {
        "name": item.get("title"),
        "article": str(item.get("id", "")),
        "price": item.get("price", {}).get("value"),
        "quantity": item.get("stocks", {}).get("quantity"),
        "image_url": (item.get("images") or [None])[0],
    }


def fetch_wb_search(text: str, limit: int = 10) -> List[Dict]:
    """
    Fetch Wildberries search via API.
    """
    api = "https://search.wb.ru/exactmatch/ru/common/v4/search"
    params = {"query": text, "limit": limit}
    sess = get_wb_session()
    sess.headers.update({
        "Accept": "application/json, text/plain, */*",
        "Referer": f"https://www.wildberries.ru/catalog/0/search.aspx?search={text}"
    })
    r = sess.get(api, params=params, timeout=15)
    try:
        r.raise_for_status()
    except Exception:
        return []
    data = r.json().get("data", {}).get("products", [])
    return [
        {
            "name": p.get("name"),
            "article": str(p.get("id", "")),
            "price": p.get("price", {}).get("sale"),
            "quantity": "",
            "image_url": p.get("imageUrl"),
        }
        for p in data[:limit]
    ]
