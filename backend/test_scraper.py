# backend/test_scraper.py
from scraper import MarketplaceScraper

def main():
    s = MarketplaceScraper()

    for market in ("Ozon", "Wildberries"):
        items = s.scrape_category(market, "хлебцы")
        print(f"\n=== {market} | хлебцы ===")
        print(f"Found {len(items)} items:")
        for i, p in enumerate(items, 1):
            print(f" {i}. {p['name']} — SKU {p['sku']} — {p['price']} ₽ — image={p['image']}")

    # И пример одного товара:
    print("\n=== Ozon single product ===")
    p = s.scrape_product("Ozon", "https://www.ozon.ru/product/hlebtsy-3-zlaka-solenye-1000-g-1605229466/")
    print(p)

    print("\n=== WB single product ===")
    p = s.scrape_product("Wildberries", "https://www.wildberries.ru/catalog/228598643/detail.aspx")
    print(p)

    s.session.close()

if __name__ == "__main__":
    main()
