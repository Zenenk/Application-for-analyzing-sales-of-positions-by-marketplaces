import logging
import re
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urljoin
from backend.utils.marketplace_urls import build_search_url, build_product_url
import requests
import urllib.parse

logger = logging.getLogger(__name__)
# Вспомогательная JS-функция для encodeURIComponent
def encodeURIComponent(x: str) -> str:
    # простая обёртка, так как Playwright передаёт строку напрямую, а в JS мы вызываем
    return urllib.parse.quote_plus(x)


class MarketplaceScraper:
    def __init__(self):
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            headless=True,
            slow_mo=50,
            args=["--disable-blink-features=AutomationControlled"]
        )
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/114.0.0.0 Safari/537.36"
        )
        self._user_agent = ua
        self._context = self._browser.new_context(
            viewport={"width": 1366, "height": 768},
            user_agent=ua,
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            java_script_enabled=True,
            bypass_csp=True,
            extra_http_headers={"Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7"}
        )

    def close(self):
        try:
            self._browser.close()
            self._pw.stop()
        except Exception:
            logger.exception("Ошибка при закрытии браузера")

    def _human_scroll(self, page):
        height = page.evaluate("() => document.body.scrollHeight") or 0
        viewport = page.evaluate("() => window.innerHeight") or 0
        for frac in [i/10 for i in range(11)]:
            y = int(frac * (height - viewport))
            page.mouse.wheel(0, y - page.evaluate("() => window.scrollY"))
            time.sleep(random.uniform(0.2, 0.5))

    def _human_mouse_move(self, page):
        box = page.viewport_size
        if not box:
            return
        w, h = box["width"], box["height"]
        page.mouse.move(w//2, h//2)
        for _ in range(random.randint(5,15)):
            x, y = random.randint(0,w), random.randint(0,h)
            page.mouse.move(x, y, steps=random.randint(5,25))
            time.sleep(random.uniform(0.1,0.3))

    def _human_delay(self, a=1, b=3):
        time.sleep(random.uniform(a,b))

    def scrape_product(self, marketplace: str, url: str) -> dict:
        page = self._context.new_page()
        result = {
            "url": url,
            "name": None,
            "article": None,
            "price": None,
            "quantity": None,
            "image_url": None,
            "price_old": None,
            "price_new": None,
            "discount": None,
            "promo_labels": []
        }
        try:
            # анти-бот
            self._human_mouse_move(page)
            page.keyboard.press(random.choice(["Tab","ArrowDown","ArrowUp"]))
            self._human_delay(0.5,1.5)

            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)

            # имитация чтения
            self._human_scroll(page)
            self._human_delay(2,5)
            t = random.uniform(15,60)
            logger.info(f"Human-like reading time: {t:.0f}s for {url}")
            time.sleep(t)

            # общий блок: парсим meta description для названия и артикула, если Wildberries
            if "wildberries.ru" in url:
                try:
                    desc = page.locator('meta[name="description"]').get_attribute('content') or ''
                    m = re.match(r'^(.*?)\s+(\d+)\s+купить', desc)
                    if m:
                        result['name'], result['article'] = m.group(1), m.group(2)
                except Exception:
                    pass

            if marketplace.lower() == "ozon":
                # изображение товара
                try:
                    result["image_url"] = page.locator(
                        "#layoutPage > div.b6 > div.container.c > div.r1l_28.l5r_28.l7r_28 "
                        "> div.r1l_28.l8r_28.l5r_28 > div.r1l_28.l5r_28.lr7_28.l3r_28 "
                        "> div.r1l_28.rl4_28.l5r_28 > div > div > div > div > div > div "
                        "> div.lq2_28 > div.ok1_28.ql6_28 > div > img"
                    ).get_attribute("src")
                except Exception:
                    pass

                # название
                try:
                    name = page.locator(
                        "#layoutPage > div.b6 > div.container.c > div.r1l_28.l5r_28.l7r_28 "
                        "> div.r1l_28.l8r_28.l5r_28 > div.r1l_28.l5r_28.lr7_28.l3r_28 "
                        "> div.r1l_28.l8r_28.l5r_28 > div > div > div > div.q2m_28 > h1"
                    ).text_content()
                    result["name"] = name.strip() if name else None
                except Exception:
                    pass

                # основной price
                try:
                    price_text = page.locator(
                        "#layoutPage > div.b6 > div.container.c > div.r1l_28.l5r_28.l7r_28 "
                        "> div.mw6_28 > div > div > div.r1l_28.l8r_28.l5r_28.r5l_28 "
                        "> div.m3s_28.sm5_28 > div > div.sm3_28 > div > div > div.mp2_28 "
                        "> div.mo9_28.a2100-a.a2100-a3 > button > span > div > div.n1k_28.k2n_28 "
                        "> div > div > span"
                    ).text_content()
                    result["price"] = float(re.sub(r"[^\d,\.]", "", price_text).replace(",", "."))
                except Exception:
                    pass

                # остатки
                try:
                    qty = page.locator(
                        "#layoutPage > div.b6 > div.container.c > div.r1l_28.l5r_28.l7r_28 "
                        "> div.mw6_28 > div > div > div.r1l_28.l8r_28.l5r_28.r5l_28 "
                        "> div.b5g_3.gb5_3 > a.q4b012-a.bg6_3.gb5_3 > div.b6g_3 "
                        "> div.gb4_3 > div.bq022-a.bq022-a4.bq022-a5.g4b_3 > span"
                    ).text_content()
                    result["quantity"] = qty.strip() if qty else None
                except Exception:
                    pass

                # новые/старые цены и скидка
                try:
                    result["price_new"] = page.locator(".m4p_28.p6m_28").text_content().strip()
                except Exception:
                    pass
                try:
                    result["price_old"] = page.locator("span.qm0_28:nth-child(2)").text_content().strip()
                except Exception:
                    pass
                try:
                    result["discount"] = page.locator(
                        ".lt1_28 > div:nth-child(1) > div:nth-child(1)"
                    ).text_content().strip()
                except Exception:
                    pass
                try:
                    labels = page.locator(".bg8_3 > span:nth-child(1)").all_text_contents()
                    result["promo_labels"] = [t.strip() for t in labels if t.strip()]
                except Exception:
                    pass

            else:  # Wildberries product page
                # изображение
                try:
                    result["image_url"] = page.locator(
                        "#imageContainer > div > div > img"
                    ).get_attribute("src")
                except Exception:
                    pass

                # название (если не получено через meta)
                if not result["name"]:
                    try:
                        name = page.locator(
                            "#\\34 327ebfa-574a-2bfb-281e-85e5de2ff193 "
                            "> div.product-page__grid > div.product-page__header-wrap "
                            "> div.product-page__header > h1"
                        ).text_content()
                        result["name"] = name.strip() if name else None
                    except Exception:
                        pass

                # цена
                try:
                    price_text = page.locator(
                        "#\\34 327ebfa-574a-2bfb-281e-85e5de2ff193 "
                        "> div.product-page__grid > div.product-page__top-blocks.hide-desktop "
                        "> div.product-page__price-block.product-page__price-block--common "
                        "> div.product-page__price-block-wrap > div > div > div > p > span > span"
                    ).text_content()
                    result["price"] = float(re.sub(r"[^\d,\.]", "", price_text).replace(",", "."))
                except Exception:
                    pass

                # новые и старые цены на карточке
                try:
                    new_p = page.locator(
                        "div.product-page__price-block:nth-child(3) > div:nth-child(6) "
                        "> div:nth-child(3) > div:nth-child(1) > p:nth-child(2) "
                        "> span:nth-child(1) > span:nth-child(3)"
                    ).text_content().strip()
                    result["price_new"] = new_p
                except Exception:
                    pass
                try:
                    old_p = page.locator(
                        "div.product-page__price-block:nth-child(3) > div:nth-child(6) "
                        "> div:nth-child(3) > div:nth-child(1) > p:nth-child(2) "
                        "> del:nth-child(3) > span:nth-child(1)"
                    ).text_content().strip()
                    result["price_old"] = old_p
                except Exception:
                    pass
                # скидка расчет или селектор
                if result.get("price_old") and result.get("price_new"):
                    try:
                        old_f = float(re.sub(r"[^\d,\.]", "", result["price_old"]).replace(",", "."))
                        new_f = float(re.sub(r"[^\d,\.]", "", result["price_new"]).replace(",", "."))
                        result["discount"] = f"{(old_f-new_f)/old_f*100:.0f}%"
                    except Exception:
                        pass

                # промо-лейблы
                labels = []
                for sel in [
                    "div.spec-action:nth-child(1) > a:nth-child(4)",
                    "div.product-page__badges:nth-child(4) > div:nth-child(7) > span:nth-child(1)"
                ]:
                    try:
                        texts = page.locator(sel).all_text_contents()
                        labels += [t.strip() for t in texts if t.strip()]
                    except Exception:
                        pass
                    self._human_delay(1,3)
                result["promo_labels"] = labels

        except Exception:
            logger.exception(f"Error scraping product {url}")
        finally:
            page.close()
        return result
    






    def _scrape_ozon_category_by_url(self, url: str, limit: int):
        """
        Скрапинг категории Ozon по готовому URL через встроенный JSON-API в контексте
        браузера (чтобы автоматически передать все антибот-куки и заголовки).
        """
        logger.info(f"[OZON-CAT] {url} ⏳")
        page = self._context.new_page()
        products = []
        try:
            # анти-ботовая подготовка
            self._human_mouse_move(page)
            page.keyboard.press(random.choice(["Tab", "ArrowDown", "ArrowUp"]))
            self._human_delay(0.5, 1.5)

            # заходим на категорию, чтобы получить нужные куки и заголовки
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            self._human_scroll(page)

            # вытягиваем чистый путь без параметров
            category_path = url.split("?", 1)[0]

            # вызываем composer-API прямо из браузера (там же уже лежат куки и UA)
            api_url = (
                "/api/composer-api.bx/page/json/v2"
                f"?url={encodeURIComponent(category_path)}"
                "&_withText=true"
                "&_binds=[\"searchResultsV2\"]"
            )
            # выполняем fetch внутри страницы
            payload = page.evaluate(
                """async (api) => {
                    const resp = await fetch(api, {
                        credentials: 'include',
                        headers: {
                            'Accept': 'application/json, text/plain, */*',
                            'Accept-Language': 'ru-RU,ru;q=0.9'
                        }
                    });
                    return await resp.json();
                }""",
                api_url
            )

            # парсим ответ
            items = (
                payload
                .get("widgetStates", {})
                .get("searchResultsV2", {})
                .get("data", {})
                .get("items", [])
            )

            for ent in items[:limit]:
                e = ent.get("entity", {})
                link      = e.get("link", "")
                article   = str(e.get("id")) or None
                name      = e.get("title")
                images    = e.get("images", [])
                img_url   = images[0].get("url") if images else None
                price_obj = e.get("price", {})
                new_p     = price_obj.get("value")
                old_p     = price_obj.get("oldValue")
                disc      = price_obj.get("discount")
                stock_obj = e.get("stock", {}).get("items", [])
                qty       = stock_obj[0].get("count") if stock_obj else None
                badges    = e.get("badges", [])
                promo_lbl = [b.get("text") for b in badges if b.get("text")]

                products.append({
                    "url":           f"https://www.ozon.ru{link}",
                    "name":          name,
                    "article":       article,
                    "price":         new_p,
                    "quantity":      qty,
                    "image_url":     img_url,
                    "price_new":     new_p,
                    "price_old":     old_p,
                    "discount":      f"{disc}%" if disc is not None else None,
                    "promo_labels":  promo_lbl
                })

        except Exception:
            logger.exception(f"Error scraping OZON category {url}")
        finally:
            page.close()

        logger.info(f"[OZON-CAT] extracted {len(products)} items")
        return products











    def _scrape_wb_category_by_url(self, url: str, limit: int):
        logger.info(f"[WB-CAT] {url} ⏳")
        page = self._context.new_page()
        products = []
        try:
            self._human_mouse_move(page)
            page.keyboard.press(random.choice(["Tab","ArrowDown","ArrowUp"]))
            self._human_delay(0.5,1.5)

            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle", timeout=15000)
            self._human_scroll(page)

            cards = page.locator("div.product-card__wrapper")
            total = min(cards.count(), limit)
            logger.info(f"[WB-CAT] found {total} cards")
            
            for i in range(total):
                card = cards.nth(i)
                # ссылка на товар
                href = card.locator("a.j-card-link").get_attribute("href") or ""
                # вытаскиваем артикул из URL
                m = re.search(r"/catalog/(\d+)/", href)
                article = m.group(1) if m else None
                # изображение
                img = card.locator(
                    "div.product-card__top-wrap > div.product-card__img-wrap.img-plug.j-thumbnail-wrap > img"
                ).get_attribute("src") or None
                # название категории-товара
                brand = card.locator("span.product-card__brand").text_content().strip() or ''
                name_part = card.locator("span.product-card__name").text_content().strip() or ''
                title = f"{brand} {name_part}".strip()
                # цена в списке
                price_text = card.locator("div.product-card__middle-wrap > div > span > ins").text_content()
                price = None
                try:
                    price = float(re.sub(r"[^\d,\.]", "", price_text).replace(",", "."))
                except Exception:
                    pass

                if article:
                    products.append({
                        "url": href,        # уже полный URL
                        "name": title,
                        "article": article,
                        "price": price,
                        "quantity": "",     # WB в категории не показывает остатки
                        "image_url": img,
                        "price_new": None,
                        "price_old": None,
                        "discount": None,
                        "promo_labels": []
                    })
                else:
                    logger.warning(f"[WB-CAT] не удалось найти артикул в карточке #{i}")

                time.sleep(random.uniform(5,30))

        except Exception:
            logger.exception(f"Error scraping WB category {url}")
        finally:
            page.close()
        return products


def scrape_marketplace(
    url: str,
    category_filter: list[str] | None = None,
    article_filter: list[str] | None = None,
    limit: int = 10,
    marketplace: str | None = None,
):
    mp = MarketplaceScraper()
    try:
        if "ozon.ru/category/" in url:
            prods = mp._scrape_ozon_category_by_url(url, limit)
        elif "wildberries.ru/catalog/0/search.aspx" in url:
            prods = mp._scrape_wb_category_by_url(url, limit)
        else:
            mpn = "ozon" if "ozon.ru" in url else "wildberries"
            prods = [ mp.scrape_product(mpn, url) ]

        if category_filter:
            prods = [
                p for p in prods
                if any(cf.lower() in (p.get("name") or "").lower() for cf in category_filter)
            ]
        if article_filter:
            prods = [ p for p in prods if p.get("article") in article_filter ]

        return prods[:limit]
    finally:
        mp.close()
