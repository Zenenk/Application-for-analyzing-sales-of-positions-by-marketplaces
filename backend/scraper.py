# scraper.py

import re
import time
import random
import requests
from urllib.parse import urlparse, parse_qs

import config_parser

# Playwright for robust browser automation
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from playwright_stealth import stealth_sync

# Selenium fallback with undetected-chromedriver
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


class MarketplaceScraper:
    """
    Универсальный скрапер для Ozon и Wildberries с основным движком Playwright (stealth)
    и резервным — Selenium + undetected-chromedriver.
    Поддерживает парсинг как категорий (первые 10 товаров), так и отдельных карточек.
    """

    def __init__(self):
        # Читаем глобальные настройки из config_parser
        self.engine = config_parser.ENGINE.lower()       # 'playwright' или 'selenium'
        self.headless = config_parser.HEADLESS           # True/False
        self.use_stealth = config_parser.USE_STEALTH     # True/False
        self.proxy = config_parser.PROXY                 # строка прокси или None
        self.user_agent = config_parser.get_random_ua()  # случайный или фиксированный UA

        if self.engine == 'playwright':
            self._init_playwright()
        elif self.engine == 'selenium':
            self._init_selenium()
        else:
            raise ValueError(f"Unsupported engine: {self.engine}")

    def _init_playwright(self):
        # Инициализируем Playwright + stealth
        self.play = sync_playwright().start()
        browser_args = {}
        if self.proxy:
            browser_args['proxy'] = {'server': self.proxy}
        self.browser = self.play.chromium.launch(headless=self.headless, **browser_args)

        context_args = {
            'user_agent': self.user_agent,
            'viewport': {'width': 1920, 'height': 1080},
            'locale': 'ru-RU',
            'java_script_enabled': True
        }
        self.context = self.browser.new_context(**context_args)
        if self.use_stealth:
            stealth_sync(self.context)
        self.page = self.context.new_page()

    def _init_selenium(self):
        # Инициализируем Selenium с undetected-chromedriver
        options = uc.ChromeOptions()
        if self.headless:
            options.headless = True
        options.add_argument("--disable-blink-features=AutomationControlled")
        if self.user_agent:
            options.add_argument(f"--user-agent={self.user_agent}")
        if self.proxy:
            options.add_argument(f"--proxy-server={self.proxy}")
        self.driver = uc.Chrome(options=options)
        self.driver.set_window_size(1920, 1080)

    def close(self):
        # Корректное завершение всех сессий
        if self.engine == 'playwright':
            try:
                self.browser.close()
                self.play.stop()
            except Exception:
                pass
        else:
            try:
                self.driver.quit()
            except Exception:
                pass

    # ——— Playwright-сессия ————————————————————————————————————————————

    def load_page_playwright(self, url: str, timeout: int = 30000) -> str:
        """
        Загружает страницу через Playwright, ждёт networkidle, обходит JS-челленджи.
        """
        try:
            self.page.goto(url, wait_until='networkidle', timeout=timeout)
        except PlaywrightTimeoutError:
            print(f"[Playwright] Timeout loading {url}")
        content = self.page.content()
        # Простой детектор антибот-страницы
        if 'captcha' in content.lower() or 'доступ ограничен' in content.lower():
            print("[Playwright] Detected bot challenge, waiting extra...")
            self.page.wait_for_timeout(5000)
            content = self.page.content()
        return content

    def simulate_user_behavior(self):
        """
        Эмулирует прокрутку и движение мыши, чтобы «оживить» поведение.
        """
        height = self.page.evaluate("() => document.body.scrollHeight")
        step = max(height // 5, 200)
        for _ in range(5):
            self.page.mouse.wheel(0, step)
            self.page.wait_for_timeout(random.uniform(500, 1000))
        # Случайное движение мыши
        w, h = 1920, 1080
        self.page.mouse.move(random.randint(0, w), random.randint(0, h), steps=10)

    # ——— Selenium-сессия (резерв) —————————————————————————————————————————

    def load_page_selenium(self, url: str) -> str:
        """
        Загружает страницу через Selenium + uc, прокручивает и ждёт.
        """
        self.driver.get(url)
        time.sleep(random.uniform(2, 4))
        self.driver.execute_script("window.scrollBy(0, document.body.scrollHeight);")
        time.sleep(1)
        return self.driver.page_source

    # ——— Wildberries через JSON-API ——————————————————————————————————————

    def extract_wb_id(self, url: str) -> str:
        """
        Извлекает числовой ID товара из URL Wildberries.
        """
        m = re.search(r'/(\d+)/', urlparse(url).path)
        return m.group(1) if m else None

    def fetch_wb_api(self, url: str) -> dict:
        """
        Получает полную информацию о карточке товара Wildberries через их JSON-API.
        """
        wb_id = self.extract_wb_id(url)
        api_url = f"https://card.wb.ru/cards/detail?appType=1&curr=rub&nm={wb_id}"
        headers = {'User-Agent': self.user_agent}
        resp = requests.get(api_url, headers=headers, timeout=15)
        resp.raise_for_status()
        products = resp.json().get('data', {}).get('products', [])
        if not products:
            return {}
        prod = products[0]

        # Формируем результат
        name = prod.get('name')
        price = (prod.get('salePriceU') or prod.get('priceU') or 0) / 100
        sku = prod.get('id')
        stock = sum(
            s.get('qty', 0)
            for size in prod.get('sizes', [])
            for s in size.get('stocks', [])
        )
        # URL главного изображения
        image = None
        if sku:
            image = f"https://images.wbstatic.net/big/new/{sku//10000}/{sku}-1.jpg"

        return {
            'name': name,
            'sku': sku,
            'price': price,
            'stock': stock,
            'image': image
        }

    def fetch_wb_category_api(self, query_or_url: str) -> list[dict]:
        """
        Получает первые 10 товаров по запросу (категории) Wildberries через API поиска.
        """
        # Определяем сам поисковый запрос
        if query_or_url.startswith('http'):
            params = parse_qs(urlparse(query_or_url).query)
            query = (params.get('query') or params.get('text') or [''])[0]
        else:
            query = query_or_url

        api_url = (
            f"https://search.wb.ru/exactmatch/ru/common/v4/search"
            f"?appType=1&curr=rub&query={query}&page=1"
        )
        headers = {'User-Agent': self.user_agent}
        resp = requests.get(api_url, headers=headers, timeout=15)
        resp.raise_for_status()
        products = resp.json().get('data', {}).get('products', [])[:10]

        results = []
        for prod in products:
            sku = prod.get('id')
            name = prod.get('name')
            price = (prod.get('salePriceU') or prod.get('priceU') or 0) / 100
            image = None
            if sku:
                image = f"https://images.wbstatic.net/big/new/{sku//10000}/{sku}-1.jpg"
            results.append({'name': name, 'sku': sku, 'price': price, 'image': image})
        return results

    # ——— Ozon —————————————————————————————————————————————————————————

    def extract_ozon_id(self, url: str) -> str:
        """
        Извлекает числовой ID товара Ozon из URL.
        """
        m = re.search(r'-(\d+)/', url)
        return m.group(1) if m else None

    def parse_ozon_page_playwright(self) -> dict:
        """
        После загрузки страницы Ozon через Playwright собирает нужные поля.
        """
        sel = config_parser.SELECTORS.get('ozon', {})
        # Название
        title = self.page.text_content(sel.get('title', '')) or ''
        # Цена
        price_text = self.page.text_content(sel.get('price', '')) or ''
        price_digits = re.sub(r'[^\d]', '', price_text)
        price = int(price_digits) if price_digits else None
        # SKU / артикул
        sku = None
        sku_sel = sel.get('sku')
        if sku_sel:
            sku_text = self.page.text_content(sku_sel) or ''
            sku = sku_text.split(':')[-1].strip()
        # Остаток
        stock = None
        stock_sel = sel.get('stock_label')
        if stock_sel:
            st = self.page.text_content(stock_sel) or ''
            m = re.search(r'(\d+)', st)
            if m:
                stock = int(m.group(1))
        # Изображение
        img = None
        img_sel = sel.get('image')
        if img_sel:
            img = self.page.get_attribute(img_sel, 'src') or self.page.get_attribute(img_sel, 'data-src')

        return {
            'name': title,
            'sku': sku,
            'price': price,
            'stock': stock,
            'image': img
        }

    def parse_ozon_page_selenium(self) -> dict:
        """
        После загрузки страницы Ozon через Selenium собирает нужные поля.
        """
        sel = config_parser.SELECTORS.get('ozon', {})

        def _get_text(by, locator):
            try:
                return self.driver.find_element(by, locator).text
            except NoSuchElementException:
                return ''

        # Название
        title = _get_text(By.CSS_SELECTOR, sel.get('title', ''))
        # Цена
        price_text = _get_text(By.CSS_SELECTOR, sel.get('price', ''))
        m_price = re.search(r'(\d+)', price_text.replace(' ', ''))
        price = int(m_price.group(1)) if m_price else None
        # SKU
        sku = None
        sku_locator = sel.get('sku')
        if sku_locator:
            by = By.XPATH if sku_locator.startswith('//') else By.CSS_SELECTOR
            sku_text = _get_text(by, sku_locator)
            sku = sku_text.split(':')[-1].strip() if sku_text else None
        # Остаток
        stock = None
        stock_locator = sel.get('stock_label')
        if stock_locator:
            by = By.XPATH if stock_locator.startswith('//') else By.CSS_SELECTOR
            st = _get_text(by, stock_locator)
            m = re.search(r'(\d+)', st)
            if m:
                stock = int(m.group(1))
        # Изображение
        img = None
        img_locator = sel.get('image')
        if img_locator:
            try:
                elem = self.driver.find_element(By.CSS_SELECTOR, img_locator)
            except NoSuchElementException:
                elem = self.driver.find_element(By.XPATH, img_locator)
            img = elem.get_attribute('src') or elem.get_attribute('data-src')

        return {
            'name': title,
            'sku': sku,
            'price': price,
            'stock': stock,
            'image': img
        }

    # ——— Публичные методы —————————————————————————————————————————————

    def scrape_product(self, platform: str, url: str) -> dict:
        """
        Собирает данные по одной карточке товара.
        Для Wildberries пытается через API, иначе fallback на браузер.
        Для Ozon — через Playwright или Selenium в зависимости от engine.
        """
        platform = platform.lower()
        if platform == 'wildberries':
            try:
                return self.fetch_wb_api(url)
            except Exception as e:
                print(f"[WB API] Error {e}, fallback to browser...")
                # тут можно реализовать Playwright/Selenium-парсинг аналогично Ozon
                # но API обычно стабилен, поэтому опускаем
                return {}

        elif platform == 'ozon':
            if self.engine == 'playwright':
                self.load_page_playwright(url)
                self.simulate_user_behavior()
                return self.parse_ozon_page_playwright()
            else:
                html = self.load_page_selenium(url)
                return self.parse_ozon_page_selenium()

        else:
            raise ValueError(f"Unsupported platform: {platform}")

    def scrape_category(self, platform: str, category_or_url: str) -> list[dict]:
        """
        Собирает первые 10 товаров по категории (или поисковому запросу).
        Для Wildberries — через API поиска.
        Для Ozon — через Playwright или Selenium, вытягивает ссылки и вызывает scrape_product.
        """
        platform = platform.lower()
        results = []

        if platform == 'wildberries':
            return self.fetch_wb_category_api(category_or_url)

        elif platform == 'ozon':
            # Формируем URL категории, если передали текст
            if category_or_url.startswith('http'):
                url = category_or_url
            else:
                url = f"https://www.ozon.ru/search/?text={category_or_url}"

            # Загружаем и эмулируем поведение
            self.load_page_playwright(url)
            self.simulate_user_behavior()

            # Собираем первые 10 уникальных ссылок на товары
            hrefs = []
            for elem in self.page.query_selector_all("a[href*='/product/']"):
                href = elem.get_attribute('href')
                if href and href not in hrefs:
                    hrefs.append(href)
                if len(hrefs) >= 10:
                    break

            # Парсим каждую карточку
            for href in hrefs:
                full_url = href if href.startswith('http') else f"https://www.ozon.ru{href}"
                info = self.scrape_product('ozon', full_url)
                results.append(info)
                time.sleep(random.uniform(1, 2))  # пауза между запросами

            return results

        else:
            raise ValueError(f"Unsupported platform: {platform}")
