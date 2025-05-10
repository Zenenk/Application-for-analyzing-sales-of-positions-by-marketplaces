from backend.scraper import fetch_ozon_product

url = "https://www.ozon.ru/product/hlebtsy-bez-glyutena-take-a-bite-assorti-5-vkusov-s-prirodnymi-vitaminami-dieticheskie-1783078110/?at=A6tGK9rKnc4noJ5pTwxNR6WfPnk9q3S6Ok31vcRmP2y6"
prod = fetch_ozon_product(url)
print("Product:", prod)
