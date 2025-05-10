#!/usr/bin/env python3
import sys
from pathlib import Path
from urllib.parse import urlparse
from backend.config_parser import read_config
from backend.scraper import scrape_marketplace

def test_url(url: str, dump_file: str, limit: int = 5):
    print(f"\n=== Testing URL ===\n{url}\n→ Dump: {dump_file}")
    products = scrape_marketplace(
        url,
        category_filter=None,
        article_filter=None,
        limit=limit,
        save_html=dump_file
    )
    print(f"Returned {len(products)} items:")
    for idx, p in enumerate(products, 1):
        print(f"{idx}. {p}")
    if Path(dump_file).exists():
        print(f"✅ HTML dump saved to: {dump_file}")
    else:
        print("❌ No HTML dump created")

def main():
    # 1) Берём URL(ы) из вашего конфига
    cfg = read_config("config/config.conf")
    raw = cfg.get("SEARCH", {}).get("urls", "")
    urls = [u.strip() for u in raw.split(",") if u.strip()]

    # 2) Протестировать каждый URL из конфигурации
    for i, u in enumerate(urls, start=1):
        test_url(u, f"dump_cfg_{i}.html")

    # 3) Тестовый Wildberries (категория)
    wb = "https://www.wildberries.ru/catalog/0/search.aspx?search=хлебцы"
    test_url(wb, "dump_wb.html")

    # 4) Тестовый Ozon — страница товара
    prod = "https://www.ozon.ru/product/hlebtsy-grechnevye-bez-soli-i-glyutena-tm-prodpostavka-15-sht-po-60-g-postnye-1636757719/"
    test_url(prod, "dump_ozon_prod.html", limit=1)

if __name__ == "__main__":
    main()
