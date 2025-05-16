import os
import configparser

def read_config(path: str) -> dict:
    """
    Считывает произвольный INI-файл по пути `path`
    и возвращает словарь вида {section: {option: value, ...}, ...}.
    """
    parser = configparser.ConfigParser(interpolation=None)
    read_files = parser.read(path, encoding="utf-8")
    if not read_files:
        raise FileNotFoundError(f"Cannot read config file at {path}")
    result = {}
    for section in parser.sections():
        result[section] = dict(parser.items(section))
    return result

# По умолчанию читаем конфиг из backend/config/config.conf или из переменной окружения CONFIG_PATH
DEFAULT_CONFIG_PATH = os.getenv(
    "CONFIG_PATH",
    os.path.join(os.path.dirname(__file__), "config", "config.conf")
)

# Загружаем его сразу при импорте
_parser = configparser.ConfigParser(interpolation=None)
_files = _parser.read(DEFAULT_CONFIG_PATH, encoding="utf-8")
if not _files:
    raise FileNotFoundError(f"Cannot read default config file at {DEFAULT_CONFIG_PATH}")

# --- SCRAPER ---
SCRAPER = {
    "user_agent": _parser.get("SCRAPER", "user_agent", fallback=""),
    "proxy": _parser.get("SCRAPER", "proxy", fallback="") or None
}

# --- MARKETPLACES ---
MARKETPLACES = [
    m.strip() for m in _parser.get("MARKETPLACES", "marketplaces", fallback="").split(",")
    if m.strip()
]

# --- SEARCH ---
SEARCH = {
    "categories": [
        c.strip() for c in _parser.get("SEARCH", "categories", fallback="").split(",")
        if c.strip()
    ],
    "urls": [
        u.strip() for u in _parser.get("SEARCH", "urls", fallback="").split(",")
        if u.strip()
    ]
}

# --- EXPORT ---
EXPORT = {
    "format": _parser.get("EXPORT", "format", fallback="CSV"),
    "save_to_db": _parser.getboolean("EXPORT", "save_to_db", fallback=True)
}
