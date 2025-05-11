# test_image_analysis.py

import os
import tempfile
import requests
from datetime import datetime

# Инициализация БД и ORM
from database import init_db, add_product, get_products
# Датчик промо-тегов
from promo_detector import PromoDetector
# Экспортер в PDF/CSV
from exporter import export_to_pdf, export_to_csv

def main():
    # 1) Инициализируем БД (создаст таблицы при необходимости)
    init_db()

    # 2) Добавляем тестовый товар
    #    Здесь можно указать URL или локальный путь к изображению
    image_url = (
        "https://sdmntprnorthcentralus.oaiusercontent.com/files/00000000-f310-622f-9498-b55533dfb99f/raw?se=2025-05-11T19%3A27%3A20Z&sp=r&sv=2024-08-04&sr=b&scid=00000000-0000-0000-0000-000000000000&skoid=1e6af1bf-6b08-4a04-8919-15773e7e7024&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-05-11T18%3A22%3A02Z&ske=2025-05-12T18%3A22%3A02Z&sks=b&skv=2024-08-04&sig=vTOOD6ZsQTVo%2BBfA4A/1uGG2VSHGZQ4kkhVq2Ow1llI%3D"
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

    # 3) Считываем все товары из БД
    prods = get_products()
    print(f"📦 Всего в БД товаров: {len(prods)}")

    # 4) Прогоняем промо-детектор по каждому товару
    detector = PromoDetector()
    results = []
    for p in prods:
        print(f"\n--- Анализ изображения для товара {p.article} ---")
        # Скачиваем картинку во временный файл
        resp = requests.get(p.image_url, timeout=10)
        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        tmp.write(resp.content)
        tmp.flush()
        tmp.close()

        # Запускаем детектор промо
        out = detector.predict_promotion(tmp.name)
        print("Результат promo-детектора:", out)

        # Собираем результаты, добавляем время парсинга
        results.append({
            "name":         p.name,
            "article":      p.article,
            "price":        p.price,
            "quantity":     p.quantity,
            "image_url":    p.image_url,
            "promotion":    out,
            "parsed_at":    datetime.utcnow()
        })

        # Удаляем временный файл
        os.remove(tmp.name)

        # 5) Экспортируем в PDF
    pdf_path = "test_report.pdf"
    export_to_pdf(results, pdf_path)
    print(f"📄 PDF-отчёт сохранён в {pdf_path}")

    # 6) Экспортируем в CSV
    csv_path = "test_report.csv"
    export_to_csv(results, csv_path)
    print(f"📑 CSV-отчёт сохранён в {csv_path}")


if __name__ == "__main__":
    main()
