"""
Модуль планировщика задач для регулярного запуска анализа.
(На данный момент не интегрирован в основной поток приложения.)
"""
import time
# Библиотеку schedule можно использовать для планирования периодических задач:
try:
    import schedule
except ImportError:
    schedule = None

def run_scheduled_analysis(config_path="config/config.conf"):
    from backend.app import app, config_parser, scraper, add_product, PromoDetector, compare_product_data, export_to_csv, export_to_pdf
    # Этот примерный метод может запускаться по расписанию для автоматического сбора и анализа данных
    with app.app_context():
        settings = config_parser.read_config(config_path)
        urls = settings.get("SEARCH", {}).get("urls", "")
        if not urls:
            return
        url_list = [url.strip() for url in urls.split(",")]
        category_filter = [cat.strip() for cat in settings.get("SEARCH", {}).get("categories", "").split(",") if cat.strip()]
        all_products = []
        for url in url_list:
            products = scraper.scrape_marketplace(url, category_filter=category_filter)
            if settings.get("EXPORT", {}).get("save_to_db", "False").lower() == "true":
                for product in products:
                    add_product(product)
            all_products.extend(products)
        # Анализ промо по аналогии с /start
        promo_detector = PromoDetector()
        for product in all_products:
            if product.get("image_url"):
                try:
                    import requests, tempfile
                    resp = requests.get(product["image_url"], timeout=10)
                    if resp.status_code == 200:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                        tmp.write(resp.content); tmp_path = tmp.name; tmp.close()
                        product["promotion_analysis"] = promo_detector.predict_promotion(tmp_path)
                        os.remove(tmp_path)
                except Exception as e:
                    product["promotion_analysis"] = {"error": str(e)}
        # Сравнение последних товаров, экспорт результатов
        if len(all_products) >= 2:
            compare_product_data(all_products[-2], all_products[-1])
        export_to_csv(all_products, "scheduled_products.csv")
        export_to_pdf(all_products, "scheduled_products.pdf")

if __name__ == "__main__":
    if schedule:
        # Планируем ежедневный запуск анализа (пример: каждый день в 02:00)
        schedule.every().day.at("02:00").do(run_scheduled_analysis)
        print("Запущен планировщик. Ожидание заданных интервалов...")
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        print("Библиотека schedule не установлена. Завершение работы.")
