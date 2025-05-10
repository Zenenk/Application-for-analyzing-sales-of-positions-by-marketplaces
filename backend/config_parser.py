import os
import random
import time
import logging
from pathlib import Path
from typing import Dict, Optional

import configparser
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

import undetected_chromedriver as uc
import shutil

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# -----------------------
# 1) Чтение конфигурации
# -----------------------

def read_config(config_file: str) -> dict:
    """
    Читает INI-файл без интерполяции '%' и возвращает словарь секций.
    """
    config_path = Path(config_file)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_file}")

    cp = configparser.RawConfigParser()
    cp.read(config_file, encoding='utf-8')

    result = {}
    for section in cp.sections():
        result[section] = dict(cp.items(section))
    return result

# -----------------------
# 2) User-Agent и прокси
# -----------------------

PROXY_LIST = [p.strip() for p in os.getenv("SCRAPER_PROXIES", "").split(",") if p.strip()]
UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.92 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.92 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.92 Safari/537.36",
]

def get_random_user_agent() -> str:
    return random.choice(UA_LIST)

def get_random_proxy() -> Optional[Dict[str, str]]:
    if not PROXY_LIST:
        return None
    p = random.choice(PROXY_LIST)
    return {"http": p, "https": p}

# -----------------------
# 3) Задержки
# -----------------------

def human_delay():
    min_d = float(os.getenv("DELAY_MIN", "2.0"))
    max_d = float(os.getenv("DELAY_MAX", "5.0"))
    delay = random.uniform(min_d, max_d)
    logger.debug(f"Human delay: {delay:.2f}s")
    time.sleep(delay)

# -----------------------
# 4) HTTP сессия
# -----------------------

def get_session() -> requests.Session:
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
# 5) Инициализация драйвера
# -----------------------

def init_driver() -> uc.Chrome:
    """
    Создает undetected_chromedriver.Chrome с автоподбором ChromeDriver.
    """
    options = uc.ChromeOptions()
    # Определяем бинарник Chromium
    chrome_path = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if chrome_path:
        options.binary_location = chrome_path

    # Headless и анти-бот флаги
    options.add_argument(f"--user-agent={get_random_user_agent()}")
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")

    proxy = get_random_proxy()
    if proxy:
        options.add_argument(f"--proxy-server={proxy['http']}")
        logger.info(f"Using proxy for Selenium: {proxy['http']}")

    driver = uc.Chrome(options=options)
    driver.implicitly_wait(10)

    # Скрываем navigator.webdriver
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"}
    )
    return driver
