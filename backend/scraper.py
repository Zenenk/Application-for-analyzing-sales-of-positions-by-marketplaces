# backend/scraper.py

import time
import random
import re
from urllib.parse import quote

from playwright.sync_api import sync_playwright, TimeoutError as PLTimeout

class MarketplaceScraper:
    def __init__(self):
        # Список реальных UA для ротации
        self._UAS = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/114.0.5735.199 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_4) AppleWebKit/605.1.15 (KHTML, like Gecko)"
            " Version/16.4 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/114.0.5735.199 Safari/537.36",
        ]

        self._pw = sync_playwright().start()

        ua = random.choice(self._UAS)
        width  = random.randint(1000, 1400)
        height = random.randint(700,  900)

        self._browser = self._pw.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        self._ctx = self._browser.new_context(
            user_agent=ua,
            viewport={"width": width, "height": height},
            locale="ru-RU",
            java_script_enabled=True,
        )
        # базовая “stealth”
        self._ctx.add_init_script(
            """() => {
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                Object.defineProperty(navigator, 'languages', {get: () => ['ru-RU','ru']});
                Object.defineProperty(navigator, 'plugins',   {get: () => [1,2,3,4,5]});
                window.chrome = {runtime: {}};
            }"""
        )
        self._log(f"Launched browser, UA={ua}, viewport={width}×{height}")

    def close(self):
        self._ctx.close()
        self._browser.close()
        self._pw.stop()

    def _log(self, msg: str):
        print(f"[Scraper] {msg}")

    def scrape_category(self, marketplace: str, query: str):
        m = marketplace.lower()
        if m == "ozon":
            return self._scrape_ozon_category(query)
        if m == "wildberries":
            return self._scrape_wb_category(query)
        raise ValueError(f"Unknown marketplace: {marketplace!r}")

    def scrape_product(self, marketplace: str, url: str):
        """Визитка товара: открываем страницу и вытаскиваем по селекторам."""
        self._log(f"scrape_product → {marketplace} @ {url}")
        page = self._ctx.new_page()
        result = {"name": None, "sku": None, "price": 0.0, "stock": None, "image": None}
        try:
            page.goto(url, timeout=60000)
            time.sleep(random.uniform(1.0, 2.5))

            if marketplace.lower()=="ozon":
                # селекторы по инспекции DevTools
                TITLE = "#layoutPage h1"
                PRICE = ("#layoutPage div.mo9_28.a2100-a.a2100-a3 "
                         "> button span div div.n1k_28.k2n_28 div div span")
                STOCK = ("#layoutPage div.b5g_3.gb5_3 "
                         "> a.q4b012-a div.b6g_3 div.gb4_3 div.bq022-a span")
                IMG   = ("#layoutPage div.lq2_28 ok1_28.ql6_28 div img")
            else:
                # Wildberries
                TITLE = "div.product-page__header h1"
                PRICE = ("div.product-page__price-block-wrap span > span")
                STOCK = None
                IMG   = "#imageContainer img"

            # ждём заголовок
            page.wait_for_selector(TITLE, timeout=30000)
            result["name"] = page.query_selector(TITLE).inner_text().strip()

            if STOCK:
                try:
                    result["stock"] = page.query_selector(STOCK).inner_text().strip()
                except:
                    result["stock"] = None

            # цена
            raw = page.query_selector(PRICE).inner_text()
            result["price"] = float(re.sub(r"[^\d,]", "", raw).replace(",", "."))

            # артикул
            m = re.search(r"(\d{5,})", url)
            result["sku"] = m.group(1) if m else None

            # картинка
            el = page.query_selector(IMG)
            result["image"] = el.get_attribute("src") if el else None

        except PLTimeout as e:
            self._log(f"Product timeout ({marketplace}): {e}")
        finally:
            page.close()

        self._log(f"Product → {result!r}")
        return result

    def _scrape_ozon_category(self, query: str):
        """Категория Ozon: рендерим страницу в браузере и парсим первые 10 карточек."""
        SEARCH = f"https://www.ozon.ru/search/?text={quote(query)}"
        SEL_CARD = "#contentScrollPaginator div[data-index]"
        self._log(f"OZON_CATEGORY: navigating to {SEARCH}")
        page = self._ctx.new_page()
        cards = []
        try:
            page.goto(SEARCH, timeout=60000)
            # плавная прокрутка вниз
            for i in range(3):
                time.sleep(random.uniform(0.5,1.0))
                page.mouse.wheel(0, random.randint(400,800))
            page.wait_for_selector(SEL_CARD, timeout=30000)

            els = page.query_selector_all(SEL_CARD)[:10]
            for c in els:
                href = c.query_selector("a").get_attribute("href")
                url = href if href.startswith("http") else "https://www.ozon.ru"+href
                cards.append(self.scrape_product("Ozon", url))
        except PLTimeout as e:
            self._log(f"OZON_CATEGORY TIMEOUT: {e}")
            snippet = page.content()[:200]
            self._log(f"OZON_CATEGORY HTML snippet: {snippet!r}")
        finally:
            page.close()

        self._log(f"OZON_CATEGORY → {len(cards)} items")
        return cards

    def _scrape_wb_category(self, query: str):
        """Категория Wildberries: рендерим страницу и парсим первые 10 карточек."""
        SEARCH = f"https://www.wildberries.ru/catalog/0/search.aspx?search={quote(query)}"
        SEL_CARD = "article.product-card.j-card-item"
        self._log(f"WB_CATEGORY: navigating to {SEARCH}")
        page = self._ctx.new_page()
        cards = []
        try:
            page.goto(SEARCH, timeout=60000)
            # плавная прокрутка
            for i in range(2):
                time.sleep(random.uniform(0.5,1.0))
                page.mouse.wheel(0, random.randint(500,900))
            page.wait_for_selector(SEL_CARD, timeout=30000)

            els = page.query_selector_all(SEL_CARD)[:10]
            for c in els:
                href = c.query_selector("a.product-card__link").get_attribute("href")
                url = href if href.startswith("http") else "https://www.wildberries.ru"+href
                cards.append(self.scrape_product("Wildberries", url))
        except PLTimeout as e:
            self._log(f"WB_CATEGORY TIMEOUT: {e}")
            snippet = page.content()[:200]
            self._log(f"WB_CATEGORY HTML snippet: {snippet!r}")
        finally:
            page.close()

        self._log(f"WB_CATEGORY → {len(cards)} items")
        return cards
