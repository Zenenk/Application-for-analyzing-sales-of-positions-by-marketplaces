# backend/config_parser.py

import os
import random
import time
import logging
import shutil
import tempfile
import configparser
import requests

from pathlib import Path
from threading import Lock
from urllib3.util.retry import Retry
from urllib3.util.url import parse_url
from urllib3.exceptions import LocationParseError

import undetected_chromedriver as uc
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException

from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def read_config(path: str) -> dict:
    """
    Read an INI-file without interpolation, return dict of sections → options.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    cp = configparser.RawConfigParser()
    cp.read(path, encoding="utf-8")
    return {section: dict(cp.items(section)) for section in cp.sections()}


def _rnd_ua() -> str:
    uas = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/136.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0) AppleWebKit/537.36 Chrome/136.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/136.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 Version/14.0 Mobile/15E148 Safari/604.1",
    ]
    return random.choice(uas)


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


def _rnd_proxy() -> dict | None:
    """
    Select a random Russian proxy from PROXIES, validate geo via ip-api.
    Return dict for requests/selenium or None.
    """
    if not PROXIES:
        return None
    random.shuffle(PROXIES)
    for url in PROXIES:
        try:
            pu = parse_url(url)
            if not pu.host or not pu.scheme:
                raise LocationParseError(url)
            r = requests.get("http://ip-api.com/json",
                             proxies={"http": url, "https": url},
                             timeout=5)
            if r.json().get("countryCode") == "RU":
                logger.debug(f"Using RU proxy: {url}")
                return {"http": url, "https": url}
        except Exception:
            continue
    logger.debug("No valid RU proxy found")
    return None


def human_delay(min_s: float = 2.0, max_s: float = 5.0):
    """
    Sleep randomly between min_s and max_s seconds.
    """
    lo = float(os.getenv("DELAY_MIN", str(min_s)))
    hi = float(os.getenv("DELAY_MAX", str(max_s)))
    time.sleep(random.uniform(lo, hi))


def _sanitize_headers(headers: dict) -> dict:
    """
    Remove any non-Latin-1 chars from header values to avoid UnicodeEncodeError.
    """
    out = {}
    for k, v in headers.items():
        if isinstance(v, str):
            out[k] = v.encode("latin-1", "ignore").decode("latin-1")
        else:
            out[k] = v
    return out


class SafeSession(requests.Session):
    """
    requests.Session subclass that sanitizes headers before sending.
    """
    def send(self, request, **kwargs):
        request.headers = _sanitize_headers(request.headers)
        return super().send(request, **kwargs)


def make_session() -> SafeSession:
    """
    Create SafeSession with:
      - Retry on 429/5xx
      - Random User-Agent
      - Accept-Language: ru
      - Russian proxy if available
    """
    session = SafeSession()
    retry = Retry(total=5, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET", "POST"])
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update({
        "User-Agent": _rnd_ua(),
        "Accept-Language": "ru-RU,ru;q=0.9"
    })
    proxy = _rnd_proxy()
    if proxy:
        session.proxies.update(proxy)
    # initial sanitize
    session.headers = _sanitize_headers(session.headers)
    return session


_STEALTH_JS = r"""
Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
window.chrome={runtime:{}};
Object.defineProperty(navigator,'languages',{get:()=>['ru-RU','ru']});
Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});
const orig=navigator.permissions.query;
navigator.permissions.query=params=>
  params.name==='notifications'?
    Promise.resolve({state:Notification.permission}):
    orig(params);
"""

_VIEWPORTS = [(1920,1080), (1366,768), (1440,900), (1600,900), (1280,720)]


def init_driver() -> uc.Chrome:
    """
    Launch undetected_chromedriver Chrome in headful mode:
      - Copy real user profile to temp to avoid locks
      - Set random UA, lang=ru, remote-debugging-port=0
      - Apply RU proxy if available
      - Inject stealth JS, timezone override
      - Attempt set_window_size, fallback maximize
    """
    # Determine source profile path
    if os.name == "nt":
        src = os.getenv("CHROME_USER_DATA_DIR") or os.path.join(
            os.getenv("LOCALAPPDATA",""), "Google", "Chrome", "User Data"
        )
    else:
        src = os.getenv("CHROME_USER_DATA_DIR") or os.path.expanduser("~/.config/google-chrome")
    tmp_dir = tempfile.mkdtemp(prefix="chrome-profile-")
    try:
        shutil.copytree(src, tmp_dir, dirs_exist_ok=True)
    except Exception:
        tmp_dir = tempfile.mkdtemp(prefix="chrome-temp-")

    opts = uc.ChromeOptions()
    opts.add_argument(f"--user-data-dir={tmp_dir}")
    opts.add_argument(f"--user-agent={_rnd_ua()}")
    opts.add_argument("--lang=ru")
    opts.add_argument("--remote-debugging-port=0")
    proxy = _rnd_proxy()
    if proxy:
        opts.add_argument(f"--proxy-server={proxy['http']}")

    driver = uc.Chrome(options=opts)
    driver.implicitly_wait(15)

    # Viewport sizing
    try:
        w, h = random.choice(_VIEWPORTS)
        driver.set_window_size(w, h)
    except WebDriverException as e:
        logger.warning(f"set_window_size failed: {e}")
        try:
            driver.maximize_window()
        except Exception:
            pass

    # Stealth and timezone
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": _STEALTH_JS})
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "Europe/Moscow"})
    return driver


def simulate_human(driver: uc.Chrome, moves: int = 8, scrolls: int = 3):
    """
    Emulate small mouse moves, scrolls, and a center click.
    """
    body = driver.find_element(By.TAG_NAME, "body")
    width = driver.execute_script("return window.innerWidth")
    height = driver.execute_script("return window.innerHeight")
    actions = ActionChains(driver).move_to_element_with_offset(body, width//2, height//2)
    for _ in range(moves):
        x = random.randint(0, width)
        y = random.randint(0, height)
        actions.move_to_element_with_offset(body, x, y).pause(random.uniform(0.1, 0.4))
    for _ in range(scrolls):
        driver.execute_script(f"window.scrollBy(0,{random.randint(200,700)});")
        time.sleep(random.uniform(0.5, 1.0))
    actions.move_to_element_with_offset(body, width//2, height//2).click().pause(random.uniform(0.2, 0.5))
    try:
        actions.perform()
    except Exception:
        pass


# --- Ozon session with Selenium + Playwright fallback ---
_OZON_LOCK = Lock()
_OZON_COOKIES: dict = {}
_OZON_TS = 0
_OZON_TTL = int(os.getenv("OZON_COOKIE_TTL", "3600"))


def _ozon_playwright_cookies() -> dict:
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=False, proxy=_rnd_proxy())
        ctx = br.new_context(
            user_agent=_rnd_ua(),
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            ignore_https_errors=True
        )
        page = ctx.new_page()
        page.goto("https://www.ozon.ru/", wait_until="networkidle")
        human_delay(3, 7)
        cookies = {c["name"]: c["value"] for c in ctx.cookies()}
        br.close()
        return cookies


def get_ozon_session() -> requests.Session:
    """
    Return a requests.Session for Ozon with human-like cookies.
    """
    global _OZON_TS, _OZON_COOKIES
    with _OZON_LOCK:
        if not _OZON_COOKIES or time.time() - _OZON_TS > _OZON_TTL:
            try:
                drv = init_driver()
                drv.get("https://www.ozon.ru/")
                simulate_human(drv)
                WebDriverWait(drv, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                _OZON_COOKIES = {c["name"]: c["value"] for c in drv.get_cookies()}
                drv.quit()
            except Exception as e:
                logger.warning(f"Selenium Ozon failed: {e}; fallback to Playwright")
                _OZON_COOKIES = _ozon_playwright_cookies()
            _OZON_TS = time.time()
    sess = make_session()
    for name, val in _OZON_COOKIES.items():
        safe = val.encode("latin-1", "ignore").decode("latin-1")
        sess.cookies.set(name, safe, domain=".ozon.ru", path="/")
    return sess


# --- Wildberries session with Selenium + Playwright fallback ---
_WB_LOCK = Lock()
_WB_COOKIES: dict = {}
_WB_TS = 0
_WB_TTL = int(os.getenv("WB_COOKIE_TTL", "600"))


def _wb_playwright_cookies() -> dict:
    with sync_playwright() as pw:
        br = pw.chromium.launch(headless=False, proxy=_rnd_proxy())
        ctx = br.new_context(
            user_agent=_rnd_ua(),
            locale="ru-RU",
            timezone_id="Europe/Moscow",
            ignore_https_errors=True
        )
        page = ctx.new_page()
        page.goto("https://www.wildberries.ru/", wait_until="networkidle")
        human_delay(3, 7)
        cookies = {c["name"]: c["value"] for c in ctx.cookies()}
        br.close()
        return cookies


def get_wb_session() -> requests.Session:
    """
    Return a requests.Session for Wildberries with human-like cookies.
    """
    global _WB_TS, _WB_COOKIES
    with _WB_LOCK:
        if not _WB_COOKIES or time.time() - _WB_TS > _WB_TTL:
            try:
                drv = init_driver()
                drv.get("https://www.wildberries.ru/")
                simulate_human(drv)
                WebDriverWait(drv, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                _WB_COOKIES = {c["name"]: c["value"] for c in drv.get_cookies()}
                drv.quit()
            except Exception as e:
                logger.warning(f"Selenium WB failed: {e}; fallback to Playwright")
                _WB_COOKIES = _wb_playwright_cookies()
            _WB_TS = time.time()
    sess = make_session()
    for name, val in _WB_COOKIES.items():
        safe = val.encode("latin-1", "ignore").decode("latin-1")
        sess.cookies.set(name, safe, domain=".wildberries.ru", path="/")
    return sess


# backward compatibility
get_session = make_session
init_driver = init_driver
