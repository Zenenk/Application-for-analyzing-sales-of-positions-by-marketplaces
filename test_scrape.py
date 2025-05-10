# test_scrape.py
import os
import json
from datetime import datetime
from backend.scraper import scrape_marketplace
from backend.exporter import export_to_csv, export_to_pdf

# Переменные окружения
os.environ["SCRAPER_PROXIES"]       = "http://user:pass@proxy1:port"
os.environ["DELAY_MIN"]             = "2"
os.environ["DELAY_MAX"]             = "5"
os.environ["OZON_COOKIE_TTL"]       = "3600"
os.environ["WB_COOKIE_TTL"]         = "600"
os.environ["SCRAPER_2CAPTCHA_KEY"]  = "ВАШ_КЛЮЧ_2CAPTCHA"

# 1) Тест поиска на Ozon
ozon = scrape_marketplace("https://www.ozon.ru/search/?text=хлебцы", limit=3)
print("OZON:", json.dumps(ozon, ensure_ascii=False, indent=2))

# 2) Тест поиска на Wildberries
wb = scrape_marketplace("https://www.wildberries.ru/catalog/0/search.aspx?search=хлебцы", limit=3)
print("WB:", json.dumps(wb, ensure_ascii=False, indent=2))

# 3) Тест экспорта
export_to_csv(ozon, "ozon_test.csv")
export_to_pdf(ozon, "ozon_test.pdf")
print("Скрипт завершён, файлы ozon_test.csv и ozon_test.pdf созданы.")
