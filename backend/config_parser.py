# backend/config_parser.py

import os
import random
import time
import logging
import shutil
import configparser
import requests

from pathlib import Path
from threading import Lock
from urllib3.util.retry import Retry
from urllib3.util.url import parse_url
from urllib3.exceptions import LocationParseError
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def read_config(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Config not found: {path}")
    cp = configparser.RawConfigParser()
    cp.read(path, encoding="utf-8")
    return {s: dict(cp.items(s)) for s in cp.sections()}


# Жёстко заданный список российских прокси
PROXIES = [
    "http://95.163.222.135:8080",
    "http://84.38.75.45:3128",
    "http://77.37.233.167:8000",
    "http://5.8.13.23:8080",
    "http://94.181.56.76:3128",
    "http://94.228.63.10:8080",
    "http://46.8.8.8:80",
    "http://109.234.31.100:3128",
    "http://185.176.27.24:8080",
    "http://188.120.242.25:8080",
]

UAS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/116.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0) AppleWebKit/537.36 Chrome/116.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/116.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 Version/14.0 Mobile/15E148 Safari/604.1",
]


def _rnd_ua() -> str:
    return random.choice(UAS)


def _rnd_proxy() -> dict | None:
    if not PROXIES:
        return None
    random.shuffle(PROXIES)
    for url in PROXIES:
        try:
            pu = parse_url(url)
            if not pu.host or not pu.scheme:
                raise LocationParseError(url)
            r = requests.get("http://ip-api.com/json", proxies={"http": url, "https": url}, timeout=5)
            if r.json().get("countryCode") == "RU":
                logger.debug(f"🇷🇺 Using RU proxy: {url}")
                return {"http": url, "https": url}
        except Exception as e:
            logger.debug(f"Skip proxy {url}: {e}")
    logger.warning("None of the proxies passed validation, returning None")
    return None


def human_delay():
    lo = float(os.getenv("DELAY_MIN", "2"))
    hi = float(os.getenv("DELAY_MAX", "5"))
    time.sleep(random.uniform(lo, hi))


def make_session() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET", "POST"]
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    s.headers.update({
        "User-Agent": _rnd_ua(),
        "Accept-Language": "ru-RU,ru;q=0.9"
    })
    proxy = _rnd_proxy()
    if proxy:
        s.proxies.update(proxy)
    return s


def _init_uc() -> uc.Chrome:
    opts = uc.ChromeOptions()
    binp = (
        shutil.which("chromium")
        or shutil.which("chromium-browser")
        or shutil.which("google-chrome")
    )
    if binp:
        opts.binary_location = binp
    opts.add_argument(f"--user-agent={_rnd_ua()}")
    opts.add_argument("--headless=new")
    opts.add_argument("--disable-blink-features=AutomationControlled")
    opts.add_argument("--lang=ru")
    proxy = _rnd_proxy()
    if proxy:
        opts.add_argument(f"--proxy-server={proxy['http']}")
    driver = uc.Chrome(options=opts)
    driver.implicitly_wait(15)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator,'webdriver',{get:() => undefined});"
    })
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "Europe/Moscow"})
    return driver


_OZON_TTL = int(os.getenv("OZON_COOKIE_TTL", "3600"))
_ozon_lock = Lock()
_ozon_cookies: dict = {}
_ozon_ts = 0


def get_ozon_session() -> requests.Session:
    global _ozon_ts, _ozon_cookies
    with _ozon_lock:
        if not _ozon_cookies or (time.time() - _ozon_ts) > _OZON_TTL:
            try:
                drv = _init_uc()
                drv.get("https://www.ozon.ru/")
                WebDriverWait(drv, 20).until(
                    lambda d: "challenge" not in d.page_source.lower()
                )
                _ozon_cookies = {c["name"]: c["value"] for c in drv.get_cookies()}
                drv.quit()
            except TimeoutException:
                logger.warning("Selenium failed CF challenge, falling back to Playwright-Stealth")
                with sync_playwright() as pw:
                    br = pw.chromium.launch(headless=True, proxy=_rnd_proxy())
                    ctx = br.new_context(
                        user_agent=_rnd_ua(),
                        locale="ru-RU",
                        timezone_id="Europe/Moscow",
                        ignore_https_errors=True
                    )
                    pg = ctx.new_page()
                    pg.goto("https://www.ozon.ru/", wait_until="networkidle")
                    human_delay()
                    _ozon_cookies = {c["name"]: c["value"] for c in ctx.cookies()}
                    br.close()
            _ozon_ts = time.time()
    session = make_session()
    for k, v in _ozon_cookies.items():
        session.cookies.set(k, v, domain=".ozon.ru", path="/")
    return session


_WB_TTL = int(os.getenv("WB_COOKIE_TTL", "600"))
_wb_lock = Lock()
_wb_cookies: dict = {}
_wb_ts = 0


def get_wb_session() -> requests.Session:
    global _wb_ts, _wb_cookies
    session = make_session()
    try:
        r = session.get("https://www.wildberries.ru/", timeout=10)
        if "need captcha" not in r.text.lower():
            return session
    except Exception:
        pass
    with _wb_lock:
        if not _wb_cookies or (time.time() - _wb_ts) > _WB_TTL:
            with sync_playwright() as pw:
                br = pw.chromium.launch(headless=True, proxy=_rnd_proxy())
                ctx = br.new_context(
                    user_agent=_rnd_ua(),
                    locale="ru-RU",
                    timezone_id="Europe/Moscow",
                    ignore_https_errors=True
                )
                pg = ctx.new_page()
                pg.goto("https://www.wildberries.ru/", wait_until="networkidle")
                human_delay()
                _wb_cookies = {c["name"]: c["value"] for c in ctx.cookies()}
                br.close()
            _wb_ts = time.time()
    for k, v in _wb_cookies.items():
        session.cookies.set(k, v, domain=".wildberries.ru", path="/")
    return session


# backward compatibility
get_session = make_session
init_driver = _init_uc
