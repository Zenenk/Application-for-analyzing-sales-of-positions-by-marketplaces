import threading
import time
import schedule
from datetime import datetime
import logging
from backend.scraper import scrape_marketplace
from backend.database import add_product, clean_old_data

logger = logging.getLogger(__name__)

# Конфигурация: здесь можно подставить значения из БД или конфиг-файла
SCRAPE_CONFIG = {
    "marketplace": "Ozon",     # либо берите из таблицы настроек
    "type":        "category", # "category" или "product"
    "query":       "хлебцы",
    "limit":       10,
    "interval":    1           # раз в X дней
}

def job_scrape_and_save():
    """
    Задача: запускает парсинг по SCRAPE_CONFIG
    и сохраняет результаты в БД.
    """
    logger.info(f"Начинаем запланированный скрапинг: {datetime.utcnow().isoformat()}")
    prods = scrape_marketplace(
        f"https://www.ozon.ru/search/?text={SCRAPE_CONFIG['query']}"
        if SCRAPE_CONFIG["type"] == "category"
        else SCRAPE_CONFIG["query"],
        category_filter=[SCRAPE_CONFIG["query"]] if SCRAPE_CONFIG["type"]=="category" else None,
        article_filter=[SCRAPE_CONFIG["query"]]  if SCRAPE_CONFIG["type"]=="product"  else None,
        limit=SCRAPE_CONFIG["limit"]
    )
    for p in prods:
        product_data = {
            "name": p.get("name",""),
            "article": p.get("article",""),
            "price": str(p.get("price","")),
            "quantity": str(p.get("quantity","")),
            "image_url": p.get("image_url",""),
            "promotion_detected": p.get("promotion_analysis",{}).get("promotion_detected",False),
            "detected_keywords": ";".join(p.get("promotion_analysis",{}).get("detected_keywords",[])),
            "price_old": p.get("price_old",""),
            "price_new": p.get("price_new",""),
            "discount": p.get("discount",""),
            "promo_labels": ";".join(p.get("promo_labels",[])),
        }
        add_product(product_data)
    logger.info("Запланированный скрапинг завершён.")

def job_cleanup():
    """
    Задача: удаляет записи старше 60 дней.
    """
    deleted = clean_old_data(60)
    logger.info(f"Очистка БД: удалено записей старее 60 дней: {deleted}")

def start_scheduler():
    """
    Регистрирует задачи и запускает цикл schedule в фоновом потоке.
    """
    # Scraping every X days
    schedule.every(SCRAPE_CONFIG["interval"]).days.do(job_scrape_and_save)
    # Cleanup daily
    schedule.every().day.at("03:00").do(job_cleanup)

    def run_loop():
        while True:
            schedule.run_pending()
            time.sleep(60)  # проверяем раз в минуту

    t = threading.Thread(target=run_loop, daemon=True)
    t.start()
    logger.info("Служба планировщика запущена.")

def update_schedule_interval(new_interval: int):
    SCRAPE_CONFIG["interval"] = new_interval
    schedule.clear("scrape_job")
    schedule.every(new_interval).days.do(job_scrape_and_save).tag("scrape_job")
    logger.info(f"Интервал обновлён: каждые {new_interval} дней")