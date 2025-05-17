import os
import tempfile

from backend.app import app
import backend.config_parser as config_parser
import backend.scraper as scraper
from backend.database import add_product
from backend.promo_detector import PromoDetector
from backend.analysis import compare_product_data
from backend.exporter import export_to_csv, export_to_pdf

def run_scheduled_analysis(config_path="config/config.conf"):
    with app.app_context():
        settings = config_parser.read_config(config_path)
        urls = settings.get("SEARCH", {}).get("urls", "")
        if not urls:
            return
        url_list = [u.strip() for u in urls.split(",") if u.strip()]
        all_products = []
        for url in url_list:
            products = scraper.scrape_marketplace(url,
                          category_filter=settings.get("SEARCH",{}).get("categories","").split(","))
            if settings.get("EXPORT",{}).get("save_to_db","False").lower()=="true":
                for p in products: add_product(p)
            all_products.extend(products)
        # экспорт файлов
        export_to_csv(all_products, "scheduled_products.csv")
        export_to_pdf(all_products, "scheduled_products.pdf")
