# config_parser.py

"""
Модуль для чтения конфигурации из INI-файла config.conf.
Разбирает секции:
  [SCRAPER]             — параметры движка и анти-бот обхода
  [SELECTORS_OZON]      — CSS/XPath-селекторы для Ozon
  [SELECTORS_WILDBERRIES] — CSS/XPath-селекторы для Wildberries
  [MARKETPLACES]        — список маркетплейсов
  [SEARCH]              — категории (запросы) и прямые URL
  [EXPORT]              — формат экспорта и флаг сохранения в БД
"""

import os
import configparser
import random

_config = configparser.ConfigParser(interpolation=None)
# Путь к INI-файлу
CONFIG_PATH = os.getenv(
    "CONFIG_PATH",
    os.path.join(os.path.dirname(__file__), "config", "config.conf")
)

# Чтение INI

_read = _config.read(CONFIG_PATH, encoding="utf-8")
if not _read:
    raise FileNotFoundError(f"Cannot read config file at {CONFIG_PATH}")

# ——— SCRAPER ————————————————————————————————————————————————————————

ENGINE      = _config.get("SCRAPER", "engine",        fallback="playwright").lower()
HEADLESS    = _config.getboolean("SCRAPER", "headless",    fallback=True)
USE_STEALTH = _config.getboolean("SCRAPER", "use_stealth", fallback=True)
_proxy_raw  = _config.get("SCRAPER", "proxy",         fallback="").strip()
PROXY       = _proxy_raw or None

# User-Agent’ы
_uas_raw      = _config.get("SCRAPER", "user_agents", fallback="")
_USER_AGENTS  = [ua.strip() for ua in _uas_raw.split(",") if ua.strip()]

def get_random_ua():
    """
    Возвращает случайный User-Agent из списка или None, если список пуст.
    """
    return random.choice(_USER_AGENTS) if _USER_AGENTS else None

# ——— SELECTORS ———————————————————————————————————————————————————————

SELECTORS = {
    "ozon": {
        "title":       _config.get("SELECTORS_OZON",    "title",       fallback=""),
        "price":       _config.get("SELECTORS_OZON",    "price",       fallback=""),
        "sku":         _config.get("SELECTORS_OZON",    "sku",         fallback=""),
        "stock_label": _config.get("SELECTORS_OZON",    "stock_label", fallback=""),
        "image":       _config.get("SELECTORS_OZON",    "image",       fallback="")
    },
    "wildberries": {
        "title":       _config.get("SELECTORS_WILDBERRIES", "title",       fallback=""),
        "price":       _config.get("SELECTORS_WILDBERRIES", "price",       fallback=""),
        "sku":         _config.get("SELECTORS_WILDBERRIES", "sku",         fallback=""),
        "stock_label": _config.get("SELECTORS_WILDBERRIES", "stock_label", fallback=""),
        "image":       _config.get("SELECTORS_WILDBERRIES", "image",       fallback="")
    }
}

def get_selector(platform: str, field: str) -> str | None:
    """
    Удобный доступ к селекторам.
    platform — 'ozon' или 'wildberries'
    field    — 'title', 'price', 'sku', 'stock_label', 'image'
    """
    return SELECTORS.get(platform.lower(), {}).get(field)

# ——— MARKETPLACES —————————————————————————————————————————————————————

_mp_raw = _config.get("MARKETPLACES", "marketplaces", fallback="")
MARKETPLACES = [m.strip() for m in _mp_raw.split(",") if m.strip()]

# ——— SEARCH ——————————————————————————————————————————————————————————

_cat_raw = _config.get("SEARCH", "categories", fallback="")
SEARCH_CATEGORIES = [c.strip() for c in _cat_raw.split(",") if c.strip()]

_url_raw = _config.get("SEARCH", "urls", fallback="")
SEARCH_URLS = [u.strip() for u in _url_raw.split(",") if u.strip()]

# ——— EXPORT ——————————————————————————————————————————————————————————

EXPORT_FORMAT = _config.get("EXPORT", "format",      fallback="CSV")
SAVE_TO_DB    = _config.getboolean("EXPORT", "save_to_db", fallback=False)


# ——— Самотестирование ——————————————————————————————————————————————————

if __name__ == "__main__":
    print("Config file       :", CONFIG_PATH)
    print("SCRAPER.engine    :", ENGINE)
    print("SCRAPER.headless  :", HEADLESS)
    print("SCRAPER.use_stealth:", USE_STEALTH)
    print("SCRAPER.proxy     :", PROXY)
    print("Random User-Agent :", get_random_ua())
    print("Ozon selectors    :", SELECTORS["ozon"])
    print("WB selectors      :", SELECTORS["wildberries"])
    print("Marketplaces      :", MARKETPLACES)
    print("Search categories :", SEARCH_CATEGORIES)
    print("Search URLs       :", SEARCH_URLS)
    print("Export.format     :", EXPORT_FORMAT)
    print("Export.save_to_db :", SAVE_TO_DB)
