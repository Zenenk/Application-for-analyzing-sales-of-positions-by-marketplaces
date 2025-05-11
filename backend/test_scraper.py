# backend/test_scraper.py
from scraper import MarketplaceScraper

def main():
    s = MarketplaceScraper()

    # 1) Wildberries — категория
    wb_list = s.scrape_category("wildberries", "хлебцы")
    print("WB items count:", len(wb_list))
    print("First two items:", wb_list[0], wb_list[1])

    # 2) Wildberries — карточка 
    wb_prod = s.scrape_product(
        "wildberries",
        "https://www.wildberries.ru/catalog/228598643/detail.aspx"
    )
    print("WB single product:", wb_prod)

    # 3) Ozon — категория
    oz_list = s.scrape_category("ozon", "хлебцы")
    print("OZ items count:", len(oz_list))
    print("First two items:", oz_list[0], oz_list[1])

    # 4) Ozon — карточка
    oz_prod = s.scrape_product(
        "ozon",
        "https://www.ozon.ru/product/hlebtsy-bez-glyutena-take-a-bite-assorti-5-vkusov-s-prirodnymi-vitaminami-dieticheskie-1783078110/?at=WPtNLzxrzC0DWAvOf5NNg4JsYXN1ODtox1wGXTE7p8Dx"
    )
    print("OZ single product:", oz_prod)

    s.close()

if __name__ == "__main__":
    main()
