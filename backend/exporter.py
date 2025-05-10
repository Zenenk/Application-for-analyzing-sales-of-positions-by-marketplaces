# exporter.py
import csv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def export_to_csv(products: list, filename: str):
    with open(filename, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["name","article","price","quantity","image_url","parsed_at"])
        writer.writeheader()
        for p in products:
            row = p.copy()
            if isinstance(row.get("parsed_at"), datetime):
                row["parsed_at"] = row["parsed_at"].isoformat()
            writer.writerow(row)

def export_to_pdf(products: list, filename: str):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    y = height - 50
    c.setFont("Helvetica", 12)
    for p in products:
        ts = p["parsed_at"].isoformat() if isinstance(p["parsed_at"], datetime) else str(p["parsed_at"])
        text = f"Название: {p['name']}, Артикул: {p['article']}, Цена: {p['price']}, Остаток: {p['quantity']}, Дата: {ts}"
        c.drawString(50, y, text)
        y -= 20
        if y < 50:
            c.showPage()
            c.setFont("Helvetica", 12)
            y = height - 50
    c.save()

if __name__ == "__main__":
    sample = [
        {"name":"Хлебцы гречневые","article":"ART123","price":100.0,"quantity":20,"image_url":"http://...","parsed_at":datetime.utcnow()},
        {"name":"Продукт 2","article":"ART456","price":200.0,"quantity":15,"image_url":"http://...","parsed_at":datetime.utcnow()},
    ]
    export_to_csv(sample, "products.csv")
    export_to_pdf(sample, "products.pdf")
    print("Done")
