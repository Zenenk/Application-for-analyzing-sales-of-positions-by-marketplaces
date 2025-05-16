# backend/test_scraper.py

from scraper import MarketplaceScraper
from backend.database import add_product

def main():
    markets = ["Ozon", "Wildberries"]
    query = "хлебцы"

    scraper = MarketplaceScraper()
    try:
        # ——— Тестируем категории ———
        for m in markets:
            print(f"\n=== {m} | {query} ===")
            items = scraper.scrape_category(m, query)
            print(f"Found {len(items)} items")
            for idx, p in enumerate(items, start=1):
                print(f" {idx}. {p['name']} — SKU {p['sku']} — {p['price']} ₽ — image={p['image']}")
                add_product({
                    "name":       p["name"],
                    "article":    p["sku"],
                    "price":      p["price"],
                    "quantity":   p.get("stock", 0),
                    "image_url":  p["image"]
                })
        
        # ——— Тестируем одиночный товар Ozon ———
        print("\n=== Ozon single product ===")
        oz_prod = scraper.scrape_product(
            "Ozon",
            "https://www.ozon.ru/product/hlebtsy-3-zlaka-solenye-1000-g-1605229466/"
        )
        print(oz_prod)

        # ——— Тестируем одиночный товар Wildberries ———
        print("\n=== Wildberries single product ===")
        wb_prod = scraper.scrape_product(
            "Wildberries",
            "https://www.wildberries.ru/catalog/228598643/detail.aspx"
        )
        print(wb_prod)

    finally:
        # Закрываем браузер
        scraper.close()


if __name__ == "__main__":
    main()
