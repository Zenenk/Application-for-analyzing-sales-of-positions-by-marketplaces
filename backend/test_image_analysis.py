# test_image_analysis.py

import os
import time
import tempfile
import requests
from datetime import datetime, timezone

# Инициализация БД и ORM
from database import init_db, add_product, get_products
# Датчик промо-тегов
from promo_detector import PromoDetector
# Экспортер отчётов (PDF + CSV)
from exporter import export_to_csv, export_to_pdf

def safe_remove(path: str, retries: int = 5, delay: float = 0.2):
    for _ in range(retries):
        try:
            os.remove(path)
            return
        except PermissionError:
            time.sleep(delay)
    print(f"⚠️ Не удалось удалить временный файл: {path}")

def main():
    init_db()

    # Добавляем тестовый товар
    image_url = (
        "https://chatgpt.com/s/m_6821231309688191ac8009fdf9542bb9"
    )
    product = {
        "name":      "Хлебцы гречневые HealthWealth",
        "article":   "123456789",
        "price":     635,
        "quantity":  42,
        "image_url": image_url
    }
    add_product(product)
    print("✅ Товар добавлен в БД:", product)

    prods = get_products()
    print(f"📦 Всего в БД товаров: {len(prods)}")

    detector = PromoDetector()
    results = []

    for p in prods:
        print(f"\n--- Анализ изображения для товара {p.article} ---")
        resp = requests.get(p.image_url, timeout=10)

        # mkstemp + close to avoid Windows lock
        fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        with open(tmp_path, "wb") as f:
            f.write(resp.content)

        out = detector.predict_promotion(tmp_path)
        print("Результат promo-детектора:", out)

        results.append({
            "name":       p.name,
            "article":    p.article,
            "price":      p.price,
            "quantity":   p.quantity,
            "image_url":  p.image_url,
            "promotion":  out,
            "parsed_at":  datetime.now(timezone.utc)
        })

        safe_remove(tmp_path)

    # **Вот это** вместо отдельных вызовов export_to_pdf/CSV
    pdf_path = export_to_pdf(results)
    csv_path = export_to_csv(results)
    print(f"\n📄 PDF-отчёт сохранён: {pdf_path}")
    print(f"📑 CSV-отчёт сохранён: {csv_path}")

if __name__ == "__main__":
    main()
