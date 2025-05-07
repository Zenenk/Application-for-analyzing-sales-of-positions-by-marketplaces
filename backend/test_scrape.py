# backend/test_scrape.py
import time
from backend.scraper import init_driver, scrape_marketplace

# 1) Инициализируем драйвер
driver = init_driver()
# 2) Открываем страницу поиска хлебцев на Ozon
url = "https://www.ozon.ru/search/?from_global=true&text=хлебцы"
driver.get(url)
time.sleep(5)  # ждём, пока JS загрузится
# 3) Запускаем вашу функцию: возвращает список словарей
products = scrape_marketplace(url, category_filter=["хлебцы"], article_filter=[])
driver.quit()

print("Найдено товаров:", len(products))
for p in products[:3]:
    print(p)
