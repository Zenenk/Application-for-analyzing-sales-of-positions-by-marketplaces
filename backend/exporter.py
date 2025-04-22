import csv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_to_csv(products, filename):
    """
    Экспортирует список продуктов в CSV файл.
    
    Аргументы:
      - products: список словарей с данными товаров.
      - filename: имя файла для сохранения.
    """
    with open(filename, mode="w", newline="", encoding="utf-8") as csv_file:
        fieldnames = ["name", "article", "price", "quantity", "image_url"]
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        for product in products:
            writer.writerow(product)

def export_to_pdf(products, filename):
    """
    Экспортирует список продуктов в PDF файл.
    
    Аргументы:
      - products: список словарей с данными товаров.
      - filename: имя файла для сохранения.
    """
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 50
    c.setFont("Helvetica", 12)
    for product in products:
        text = f"Название: {product['name']}, Артикул: {product['article']}, Цена: {product['price']}, Остаток: {product['quantity']}"
        c.drawString(50, y, text)
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50
    c.save()

if __name__ == "__main__":
    sample_products = [
        {"name": "Хлебцы гречневые", "article": "ART123", "price": "100 руб.", "quantity": "20", "image_url": "http://example.com/image1.jpg"},
        {"name": "Продукт 2", "article": "ART456", "price": "200 руб.", "quantity": "15", "image_url": "http://example.com/image2.jpg"}
    ]
    export_to_csv(sample_products, "products.csv")
    export_to_pdf(sample_products, "products.pdf")
    print("Экспорт завершен")
