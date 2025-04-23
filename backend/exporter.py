import csv
import os
import io
from datetime import datetime
from reportlab.pdfgen import canvas

def export_to_csv():
    # Здесь реализована демо-экспортовая логика – нужно заменить на выборку из БД
    data = [
        {'name': 'Товар 1', 'price': 100, 'marketplace': 'Ozon'},
        {'name': 'Товар 2', 'price': 200, 'marketplace': 'Wildberries'}
    ]
    csv_file = f'exports/report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    os.makedirs('exports', exist_ok=True)
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'price', 'marketplace'])
        writer.writeheader()
        for row in data:
            writer.writerow(row)
    return csv_file

def export_to_pdf():
    pdf_file = f'exports/report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
    os.makedirs('exports', exist_ok=True)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(50, 800, "Отчёт по мониторингу маркетплейсов")
    c.drawString(50, 780, "Демо-данные:")
    c.drawString(50, 760, "Товар 1 - 100 руб (Ozon)")
    c.drawString(50, 740, "Товар 2 - 200 руб (Wildberries)")
    c.showPage()
    c.save()
    with open(pdf_file, 'wb') as f:
        f.write(buffer.getvalue())
    return pdf_file
