# backend/scraper.py
import logging
import re
import time
import random
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)

class MarketplaceScraper:
    def __init__(self):
        self._pw = sync_playwright().start()
        # Запускаем браузер в headless режиме
        self._browser = self._pw.chromium.launch(headless=True)
        self._context = self._browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)...",
        )

    def close(self):
        """Закрывает браузерный контекст и Playwright"""
        try:
            self._browser.close()
            self._pw.stop()
        except Exception as e:
            logger.error(f"Ошибка при закрытии браузера: {e}")

    def _human_scroll(self, page):
        """
        Имитация человеческого скролла: плавное прокручивание страницы с рандомными паузами.
        """
        try:
            height = page.evaluate("() => document.body.scrollHeight") or 0
            viewport = page.evaluate("() => window.innerHeight") or 0
            # Разбиваем на 5 сегментов
            segments = [i/4 for i in range(5)]
            for frac in segments:
                y = int(frac * (height - viewport))
                page.evaluate(f"() => window.scrollTo(0, {y})")
                pause = random.uniform(5, 15)
                time.sleep(pause)
        except Exception as e:
            logger.warning(f"Human scroll warning: {e}")

    def _human_delay(self, min_sec=2, max_sec=5):
        """
        Рандомная пауза между действиями: от min_sec до max_sec секунд.
        """
        time.sleep(random.uniform(min_sec, max_sec))

    def scrape_product(self, marketplace: str, url: str) -> dict:
        """
        Скрапинг одной страницы товара с имитацией человека.
        Возвращает словарь данных.
        """
        page = self._context.new_page()
        result = {
            "url": url,
            "name": None,
            "article": None,
            "price": None,
            "quantity": None,
            "image_url": None,
            # Новые поля скидок и промо
            "price_old": None,
            "price_new": None,
            "discount": None,
            "promo_labels": []
        }
        try:
            page.goto(url, timeout=120000)
            # Ждём полной загрузки фронтенда
            page.wait_for_load_state("networkidle", timeout=60000)
            # Имитация чтения страницы пользователем
            human_read = random.uniform(60, 180)
            logger.info(f"Human-like reading time: {human_read:.1f}s for {url}")
            self._human_scroll(page)
            time.sleep(human_read)

            # Извлечение данных с рандомными паузами
            # Название
            try:
                result["name"] = page.locator("#layoutPage h1").text_content().strip()
            except PlaywrightTimeoutError:
                result["name"] = None
            self._human_delay()

            # Основная цена
            try:
                price_text = page.locator("button[data-testid='price-button'] span").text_content()
                result["price"] = float(re.sub(r"[^0-9,.]", "", price_text).replace(",", "."))
            except Exception:
                result["price"] = None
            self._human_delay()

            # Изображение
            try:
                result["image_url"] = page.locator("img[data-testid='picture-element-img']").get_attribute("src")
            except Exception:
                result["image_url"] = None
            self._human_delay()

            # Старая и новая цены, скидка, промо-лейблы
            if marketplace.lower() == "ozon":
                # Новая цена
                try:
                    result["price_new"] = page.locator(".m4p_28.p6m_28").text_content().strip()
                except Exception:
                    result["price_new"] = None
                self._human_delay()
                # Старая цена
                try:
                    result["price_old"] = page.locator("span.qm0_28:nth-child(2)").text_content().strip()
                except Exception:
                    result["price_old"] = None
                self._human_delay()
                # Скидка
                try:
                    result["discount"] = page.locator(
                        ".lt1_28 > div:nth-child(1) > div:nth-child(1)"
                    ).text_content().strip()
                except Exception:
                    result["discount"] = None
                self._human_delay()
                # Промо-лейблы
                try:
                    labels = page.locator(".bg8_3 > span:nth-child(1)").all_text_contents()
                    result["promo_labels"] = [t.strip() for t in labels if t.strip()]
                except Exception:
                    result["promo_labels"] = []
            else:
                # Wildberries
                # Новая цена
                try:
                    result["price_new"] = page.locator(
                        "div.product-page__price-block:nth-child(3) > div:nth-child(6) "
                        "> div:nth-child(3) > div:nth-child(1) > p:nth-child(2) "
                        "> span:nth-child(1) > span:nth-child(3)"
                    ).text_content().strip()
                except Exception:
                    result["price_new"] = None
                self._human_delay()
                # Старая цена
                try:
                    result["price_old"] = page.locator(
                        "div.product-page__price-block:nth-child(3) > div:nth-child(6) "
                        "> div:nth-child(3) > div:nth-child(1) > p:nth-child(2) "
                        "> del:nth-child(3) > span:nth-child(1)"
                    ).text_content().strip()
                except Exception:
                    result["price_old"] = None
                self._human_delay()
                # Вычисление скидки
                if result.get("price_old") and result.get("price_new"):
                    try:
                        old = float(re.sub(r"[^0-9,.]", "", result["price_old"]).replace(",", "."))
                        new = float(re.sub(r"[^0-9,.]", "", result["price_new"]).replace(",", "."))
                        pct = (old - new) / old * 100
                        result["discount"] = f"{pct:.0f}%"
                    except Exception:
                        result["discount"] = None
                else:
                    try:
                        result["discount"] = page.locator(
                            "div.product-page__badges:nth-child(4) > div:nth-child(7) > span:nth-child(1)"
                        ).text_content().strip()
                    except Exception:
                        result["discount"] = None
                self._human_delay()
                # Промо-лейблы
                labels = []
                for sel in [
                    "div.spec-action:nth-child(1) > a:nth-child(4)",
                    "div.product-page__badges:nth-child(4) > div:nth-child(7) > span:nth-child(1)"
                ]:
                    try:
                        texts = page.locator(sel).all_text_contents()
                        labels.extend([t.strip() for t in texts if t.strip()])
                    except Exception:
                        pass
                    self._human_delay(1, 3)
                result["promo_labels"] = labels

        except Exception as e:
            logger.error(f"Error scraping product {url}: {e}")
        finally:
            page.close()
        return result

    def _scrape_ozon_category(self, query: str, limit: int):
        """Скрапинг категории Ozon с имитацией"""
        page = self._context.new_page()
        products = []
        try:
            search_url = f"https://www.ozon.ru/search/?text={query}"
            page.goto(search_url, timeout=120000)
            page.wait_for_load_state("networkidle", timeout=60000)
            self._human_scroll(page)
            cards = page.locator("div[data-index]")
            count = min(cards.count(), limit)
            for i in range(count):
                card = page.locator("div[data-index]").nth(i)
                href = card.locator("a").get_attribute("href")
                prod = self.scrape_product("ozon", href)
                products.append(prod)
                # Пауза между товарами
                time.sleep(random.uniform(30, 90))
        except Exception as e:
            logger.error(f"Error scraping OZON category {query}: {e}")
        finally:
            page.close()
        return products

    def _scrape_wb_category(self, query: str, limit: int):
        """Скрапинг категории Wildberries с имитацией"""
        page = self._context.new_page()
        products = []
        try:
            search_url = f"https://www.wildberries.ru/catalog/0/search.aspx?search={query}"
            page.goto(search_url, timeout=120000)
            page.wait_for_load_state("networkidle", timeout=60000)
            self._human_scroll(page)
            cards = page.locator("article.product-card")
            count = min(cards.count(), limit)
            for i in range(count):
                card = page.locator("article.product-card").nth(i)
                href = card.locator("a").get_attribute("href")
                prod = self.scrape_product("wildberries", href)
                products.append(prod)
                time.sleep(random.uniform(30, 90))
        except Exception as e:
            logger.error(f"Error scraping WB category {query}: {e}")
        finally:
            page.close()
        return products


def scrape_marketplace(url, category_filter=None, article_filter=None, limit=10):
    """
    Универсальная функция: выбирает категорию или товар и возвращает список.
    """
    mp = MarketplaceScraper()
    products = []
    try:
        if "/search" in url:
            if "ozon.ru" in url:
                query = url.split("?")[1].split("=")[1]
                products = mp._scrape_ozon_category(query, limit)
            else:
                query = url.split("=")[1]
                products = mp._scrape_wb_category(query, limit)
        else:
            marketplace = "ozon" if "ozon.ru" in url else "wildberries"
            products = [mp.scrape_product(marketplace, url)]
        # Применяем фильтры
        if category_filter:
            products = [p for p in products if any(
                cat.lower() in (p.get("name") or "").lower()
                for cat in category_filter
            )]
        if article_filter:
            products = [p for p in products if p.get("article") in article_filter]
        return products[:limit]
    finally:
        mp.close()
