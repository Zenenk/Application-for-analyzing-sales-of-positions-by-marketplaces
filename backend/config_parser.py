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

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def read_config(path: str) -> dict:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Config file not found: {path}")
    cp = configparser.RawConfigParser()
    cp.read(path, encoding="utf-8")
    return {section: dict(cp.items(section)) for section in cp.sections()}


def _rnd_ua() -> str:
    return random.choice([
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/136.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 12_0) AppleWebKit/537.36 Chrome/136.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/136.0 Safari/537.36",
        "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 Version/14.0 Mobile/15E148 Safari/604.1",
    ])


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
    random.shuffle(PROXIES)
    for url in PROXIES:
        try:
            pu = parse_url(url)
            if not pu.scheme or not pu.host:
                raise LocationParseError(url)
            r = requests.get("http://ip-api.com/json", proxies={"http": url, "https": url}, timeout=5)
            if r.json().get("countryCode") == "RU":
                return {"http": url, "https": url}
        except Exception:
            continue
    return None


def human_delay(min_s: float = 2.0, max_s: float = 5.0):
    lo = float(os.getenv("DELAY_MIN", str(min_s)))
    hi = float(os.getenv("DELAY_MAX", str(max_s)))
    time.sleep(random.uniform(lo, hi))


def _sanitize_headers(headers: dict) -> dict:
    out = {}
    for k, v in headers.items():
        if isinstance(v, str):
            out[k] = v.encode("latin-1", "ignore").decode("latin-1")
        else:
            out[k] = v
    return out


class SafeSession(requests.Session):
    def send(self, req, **kwargs):
        req.headers = _sanitize_headers(req.headers)
        return super().send(req, **kwargs)


def make_session() -> SafeSession:
    sess = SafeSession()
    retry = Retry(total=5, backoff_factor=1,
                  status_forcelist=[429, 500, 502, 503, 504],
                  allowed_methods=["GET", "POST"])
    adapter = requests.adapters.HTTPAdapter(max_retries=retry)
    sess.mount("http://", adapter)
    sess.mount("https://", adapter)
    sess.headers.update({
        "User-Agent": _rnd_ua(),
        "Accept-Language": "ru-RU,ru;q=0.9",
    })
    p = _rnd_proxy()
    if p:
        sess.proxies.update(p)
    sess.headers = _sanitize_headers(sess.headers)
    return sess


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
    if os.name == "nt":
        src = os.getenv("CHROME_USER_DATA_DIR") or os.path.join(os.getenv("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
    else:
        src = os.getenv("CHROME_USER_DATA_DIR") or os.path.expanduser("~/.config/google-chrome")
    tmp = tempfile.mkdtemp(prefix="chrome-profile-")
    try:
        shutil.copytree(src, tmp, dirs_exist_ok=True)
    except Exception:
        tmp = tempfile.mkdtemp(prefix="chrome-temp-")
    opts = uc.ChromeOptions()
    opts.add_argument(f"--user-data-dir={tmp}")
    opts.add_argument(f"--user-agent={_rnd_ua()}")
    opts.add_argument("--lang=ru")
    opts.add_argument("--remote-debugging-port=0")
    pr = _rnd_proxy()
    if pr:
        opts.add_argument(f"--proxy-server={pr['http']}")
    driver = uc.Chrome(options=opts)
    driver.implicitly_wait(15)
    try:
        w, h = random.choice(_VIEWPORTS)
        driver.set_window_size(w, h)
    except WebDriverException:
        try:
            driver.maximize_window()
        except Exception:
            pass
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": _STEALTH_JS})
    driver.execute_cdp_cmd("Emulation.setTimezoneOverride", {"timezoneId": "Europe/Moscow"})
    return driver


def simulate_human(driver: uc.Chrome, moves: int = 5, scrolls: int = 2):
    body = driver.find_element(By.TAG_NAME, "body")
    w = driver.execute_script("return window.innerWidth")
    h = driver.execute_script("return window.innerHeight")
    actions = ActionChains(driver).move_to_element_with_offset(body, w//2, h//2)
    for _ in range(moves):
        x = random.randint(0, w)
        y = random.randint(0, h)
        actions.move_to_element_with_offset(body, x, y).pause(random.uniform(0.1, 0.3))
    for _ in range(scrolls):
        driver.execute_script(f"window.scrollBy(0,{random.randint(200,600)});")
        time.sleep(random.uniform(0.5, 1.0))
    actions.move_to_element_with_offset(body, w//2, h//2).click().pause(0.2)
    try:
        actions.perform()
    except Exception:
        pass


_OZON_LOCK = Lock()
_OZON_COOKIES = {}
_OZON_TS = 0
_OZON_TTL = int(os.getenv("OZON_COOKIE_TTL", "3600"))


def get_ozon_session() -> requests.Session:
    global _OZON_TS, _OZON_COOKIES
    with _OZON_LOCK:
        if not _OZON_COOKIES or time.time() - _OZON_TS > _OZON_TTL:
            drv = init_driver()
            drv.get("https://www.ozon.ru/")
            simulate_human(drv)
            WebDriverWait(drv, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            _OZON_COOKIES = {c["name"]: c["value"] for c in drv.get_cookies()}
            drv.quit()
            _OZON_TS = time.time()
    sess = make_session()
    for name, val in _OZON_COOKIES.items():
        sess.cookies.set(name, val, domain=".ozon.ru", path="/")
    return sess


_WB_LOCK = Lock()
_WB_COOKIES = {}
_WB_TS = 0
_WB_TTL = int(os.getenv("WB_COOKIE_TTL", "600"))


def get_wb_session() -> requests.Session:
    global _WB_TS, _WB_COOKIES
    with _WB_LOCK:
        if not _WB_COOKIES or time.time() - _WB_TS > _WB_TTL:
            drv = init_driver()
            drv.get("https://www.wildberries.ru/")
            simulate_human(drv)
            WebDriverWait(drv, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            _WB_COOKIES = {c["name"]: c["value"] for c in drv.get_cookies()}
            drv.quit()
            _WB_TS = time.time()
    sess = make_session()
    for name, val in _WB_COOKIES.items():
        sess.cookies.set(name, val, domain=".wildberries.ru", path="/")
    return sess


# backward compatibility
get_session = make_session
init_driver = init_driver
