# backend/scraper.py

import logging
import time
from typing import List, Dict, Optional
from urllib.parse import urlparse, parse_qs, unquote

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
from selenium.common.exceptions import WebDriverException

from backend.config_parser import _rnd_ua, _rnd_proxy, human_delay, init_driver, get_ozon_session, get_wb_session

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def scrape_marketplace(
    url: str,
    limit: int = 10,
    save_html: Optional[str] = None,
) -> List[Dict]:
    """
    Универсальный скрейпер:
      - Поисковая страница Ozon → headful Selenium + BS4
      - Поисковая страница Wildberries → headful Playwright + BS4
      - Иначе → headful Playwright + BS4
    """
    logger.info(f"🔍 scrape_marketplace URL={url}")

    if "ozon.ru/search" in url or "ozon.ru/category" in url:
        return _scrape_ozon_via_selenium(url, limit, save_html)

    if "wildberries.ru" in url:
        return _scrape_generic_via_playwright(url, limit, save_html, 
                                               selector="div.product-card",
                                               parser=_parse_wb_card)

    # Generic fallback for other sites
    return _scrape_generic_via_playwright(url, limit, save_html,
                                           selector="div.product-card",
                                           parser=_parse_generic_card)


def _scrape_ozon_via_selenium(url: str, limit: int, save_html: Optional[str]) -> List[Dict]:
    """
    Headful Selenium обход антибота для Ozon.
    """
    try:
        driver = init_driver()
        driver.get(url)
        human_delay(2, 5)
        html = driver.page_source
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
        return products
    except WebDriverException as e:
        logger.error(f"Selenium Ozon failed: {e}")
        return []


def _scrape_generic_via_playwright(
    url: str,
    limit: int,
    save_html: Optional[str],
    selector: str,
    parser
) -> List[Dict]:
    """
    Headful Playwright обход антибота для Wildberries и generic.
    `selector` — CSS селектор карточек.
    `parser` — функция (bs4.Element)->dict.
    """
    with sync_playwright() as pw:
        proxy = _rnd_proxy()
        browser = pw.chromium.launch(
            headless=False,
            proxy={"server": proxy["http"]} if proxy else None,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                f"--user-agent={_rnd_ua()}",
            ],
        )
        ctx = browser.new_context(
            user_agent=_rnd_ua(),
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            ignore_https_errors=True
        )
        page = ctx.new_page()
        page.goto(url, wait_until="networkidle")
        human_delay(2, 5)
        page.mouse.wheel(0, 1000)
        human_delay(1, 2)

        html = page.content()
        if save_html:
            with open(save_html, "w", encoding="utf-8") as f:
                f.write(html)
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select(selector)[:limit]
        products = []
        for card in cards:
            try:
                products.append(parser(card))
            except Exception:
                continue

        browser.close()
        return products


def _parse_wb_card(card) -> Dict:
    name = card.select_one("span.goods-name").get_text(strip=True)
    article = card.select_one("span.goods-id").get_text(strip=True)
    price = card.select_one("ins.lower-price").get_text(strip=True)
    img = card.select_one("img.j-picture")
    img_url = img["src"] if img and img.has_attr("src") else ""
    return {
        "name": name,
        "article": article,
        "price": price,
        "quantity": "",
        "image_url": img_url,
    }


def _parse_generic_card(card) -> Dict:
    name_el = card.select_one("h2") or card.select_one("h4") or card.select_one("span.name")
    name = name_el.get_text(strip=True) if name_el else ""
    article = card.get("data-article", "")
    price_el = card.select_one(".price") or card.select_one(".tile-price")
    price = price_el.get_text(strip=True) if price_el else ""
    img = card.select_one("img")
    img_url = img["src"] if img and img.has_attr("src") else ""
    return {
        "name": name,
        "article": article,
        "price": price,
        "quantity": "",
        "image_url": img_url,
    }
