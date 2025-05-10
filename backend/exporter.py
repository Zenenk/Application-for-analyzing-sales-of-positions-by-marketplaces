"""
Модуль экспорта списка продуктов в файлы (CSV и PDF).
"""
import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_to_csv(products, filename):
    """
    Экспортирует список продуктов (list of dicts) в CSV-файл.
    Аргументы:
      - products: список словарей с данными товаров.
      - filename: имя CSV-файла для сохранения.
    """
    with open(filename, mode="w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ["name", "article", "price", "quantity", "image_url", "parsed_at"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for product in products:
            # Парсим parsed_at в строку, если это datetime
            row = product.copy()
            if hasattr(row.get("parsed_at"), "isoformat"):
                row["parsed_at"] = row["parsed_at"].isoformat()
            writer.writerow(row)

def export_to_pdf(products, filename):
    """
    Экспортирует список продуктов в PDF-файл.
    Каждый продукт выводится отдельной строкой текста.
    Аргументы:
      - products: список словарей с данными товаров.
      - filename: имя PDF-файла для сохранения.
    """
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 50  # начальная высота для первого элемента
    c.setFont("Helvetica", 12)
    for product in products:
        parsed = product.get("parsed_at")
        ts = parsed.isoformat() if hasattr(parsed, "isoformat") else str(parsed)
        text = (
            f"Название: {product.get('name','')}, Артикул: {product.get('article','')}, "
            f"Цена: {product.get('price','')}, Остаток: {product.get('quantity','')}, "
            f"Дата парсинга: {ts}"
        )
        c.drawString(50, y, text)
        y -= 20
        # Если достигли нижней границы страницы, создаём новую страницу
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = height - 50
    c.save()

# Пример использования модулей экспорта
if __name__ == "__main__":
    sample_products = [
        {"name": "Хлебцы гречневые", "article": "ART123", "price": "100 руб.", "quantity": "20", "image_url": "http://example.com/image1.jpg"},
        {"name": "Продукт 2", "article": "ART456", "price": "200 руб.", "quantity": "15", "image_url": "http://example.com/image2.jpg"}
    ]
    export_to_csv(sample_products, "products.csv")
    export_to_pdf(sample_products, "products.pdf")
    print("Экспорт завершен.")
