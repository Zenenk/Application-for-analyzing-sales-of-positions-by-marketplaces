import os
import configparser

# Отключаем интерполяцию, чтобы '%' в url-encoded строках не резались
_config = configparser.ConfigParser(interpolation=None)

CONFIG_PATH = os.getenv(
    "CONFIG_PATH",
    os.path.join(os.path.dirname(__file__), "config", "config.conf")
)

_read = _config.read(CONFIG_PATH, encoding="utf-8")
if not _read:
    raise FileNotFoundError(f"Cannot read config file at {CONFIG_PATH}")

# SCRAPER settings
SCRAPER = {
    "user_agent": _config.get("SCRAPER", "user_agent", fallback=""),
    "proxy": _config.get("SCRAPER", "proxy", fallback="") or None
}

# Общие настройки
MARKETPLACES = [
    m.strip() for m in _config.get("MARKETPLACES", "marketplaces", fallback="").split(",")
    if m.strip()
]
SEARCH_CATEGORIES = [
    c.strip() for c in _config.get("SEARCH", "categories", fallback="").split(",")
    if c.strip()
]
SEARCH_URLS = [
    u.strip() for u in _config.get("SEARCH", "urls", fallback="").split(",")
    if u.strip()
]

EXPORT_FORMAT = _config.get("EXPORT", "format", fallback="CSV")
SAVE_TO_DB = _config.getboolean("EXPORT", "save_to_db", fallback=False)
