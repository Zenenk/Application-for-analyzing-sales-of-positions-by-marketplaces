# backend/config_parser.py
import os
import configparser


def read_config(path: str) -> dict:
    """
    Считывает INI-файл по пути `path` и возвращает структуру:
      {
        "SCRAPER":      {"user_agent": str, "proxy": str|None},
        "MARKETPLACES": {"marketplaces": [str, ...]},
        "SEARCH":       {"urls": [...], "categories": [...], "articles": [...]},
        "EXPORT":       {"format": str, "save_to_db": bool}
      }
    """
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Конфиг не найден по пути: {path}")

    cp = configparser.ConfigParser(interpolation=None)
    cp.read(path, encoding="utf-8")

    # --- SCRAPER ---
    scraper_section = "SCRAPER"
    user_agent = cp.get(scraper_section, "user_agent", fallback="")
    proxy = cp.get(scraper_section, "proxy", fallback="") or None

    # --- MARKETPLACES ---
    mp_section = "MARKETPLACES"
    mp_list = (
        cp.get(mp_section, "marketplaces", fallback="")
        .split(",")
    )
    marketplaces = [m.strip() for m in mp_list if m.strip()]

    # --- SEARCH ---
    search_section = "SEARCH"
    urls = [u.strip() for u in cp.get(search_section, "urls", "").split(",") if u.strip()]
    categories = [c.strip() for c in cp.get(search_section, "categories", "").split(",") if c.strip()]
    articles   = [a.strip() for a in cp.get(search_section, "articles",   "").split(",") if a.strip()]

    # --- EXPORT ---
    export_section = "EXPORT"
    fmt = cp.get(export_section, "format", fallback="CSV")
    save_to_db = cp.getboolean(export_section, "save_to_db", fallback=False)

    return {
        "SCRAPER":      {"user_agent": user_agent, "proxy": proxy},
        "MARKETPLACES": {"marketplaces": marketplaces},
        "SEARCH":       {"urls": urls, "categories": categories, "articles": articles},
        "EXPORT":       {"format": fmt, "save_to_db": save_to_db},
    }


# --- Default config load on import ---
DEFAULT_CONFIG_PATH = os.getenv(
    "CONFIG_PATH",
    os.path.join(os.path.dirname(__file__), "config", "config.conf")
)

_config = read_config(DEFAULT_CONFIG_PATH)

SCRAPER      = _config["SCRAPER"]
MARKETPLACES = _config["MARKETPLACES"]["marketplaces"]
SEARCH       = _config["SEARCH"]
EXPORT       = _config["EXPORT"]
