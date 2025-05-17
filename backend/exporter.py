# backend/exporter.py
import os
import csv
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from backend.database import get_product_history
import matplotlib.pyplot as plt
from io import BytesIO


# Папки для отчётов
CSV_RESULTS = "csv_results"
PDF_RESULTS = "pdf_results"

os.makedirs(CSV_RESULTS, exist_ok=True)
os.makedirs(PDF_RESULTS, exist_ok=True)

# Регистрация шрифта для кириллицы
DEJAVU_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
if not os.path.isfile(DEJAVU_PATH):
    raise RuntimeError(f"Не найден шрифт DejaVuSans по пути {DEJAVU_PATH}")
pdfmetrics.registerFont(TTFont('DejaVuSans', DEJAVU_PATH))


def export_to_csv(products, path=None):
    """
    Экспортирует список продуктов в CSV.
    Возвращает путь к файлу.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = path or os.path.join(CSV_RESULTS, f"report_{timestamp}.csv")

    fieldnames = [
        "name", "article", "price", "quantity", "image_url",
        "price_old", "price_new", "discount", "promo_labels",
        "promotion_detected", "detected_keywords", "parsed_at"
    ]

    with open(filename, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        labels = p.get("promo_labels") or []
        for p in products:
            writer.writerow({
                "name": p.get("name", ""),
                "article": p.get("article", ""),
                "price": p.get("price", ""),
                "quantity": p.get("quantity", ""),
                "image_url": p.get("image_url",""),
                "price_old": p.get("price_old", ""),
                "price_new": p.get("price_new", ""),
                "discount": p.get("discount", ""),
                "promo_labels": ";".join(labels),
                "promotion_detected": p.get("promotion_analysis", {}).get("promotion_detected", False),
                "detected_keywords": ";".join(p.get("promotion_analysis", {}).get("detected_keywords", [])),
                "parsed_at": p.get("parsed_at", datetime.now().isoformat())
            })
    return filename


def export_to_pdf(products, path=None):
    """
    Экспортирует список продуктов в PDF.
    Возвращает путь к файлу.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = path or os.path.join(PDF_RESULTS, f"report_{timestamp}.pdf")

    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'DejaVuSans'

    # Заголовки таблицы
    data = [[
        "Name", "Article", "Price", "Quantity",
        "Old Price", "New Price", "Discount", "Promo Labels",
        "Promo Detected", "Keywords", "Parsed At"
    ]]

    # Данные
    for p in products:
        row = [
            Paragraph(str(p.get("name", "")), styles['Normal']),
            str(p.get("article", "")),
            str(p.get("price", "")),
            str(p.get("quantity", "")),
            str(p.get("price_old", "")),
            str(p.get("price_new", "")),
            str(p.get("discount", "")),
            ", ".join(p.get("promo_labels", [])),
            str(p.get("promotion_analysis", {}).get("promotion_detected", False)),
            ", ".join(p.get("promotion_analysis", {}).get("detected_keywords", [])),
            p.get("parsed_at", datetime.now().isoformat())
        ]
        data.append(row)

    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
    return filename

def export_product_pdf(article: str, path: str = None) -> str:
    """
    Формирует PDF-отчёт с графиками по одному товару.
    Возвращает путь к сгенерированному файлу.
    """
    # 1. Получаем историю
    history = get_product_history(article)
    if not history:
        raise FileNotFoundError(f"No history for article {article}")

    # 2. Подготавливаем имя файла
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = path or os.path.join(PDF_RESULTS, f"{article}_{ts}.pdf")

    # 3. Создаём PDF
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    styles["Normal"].fontName = "DejaVuSans"

    elements = []
    elements.append(Paragraph(f"Отчёт по товару: {article}", styles["Title"]))
    elements.append(Spacer(1, 12))

    # 4. По каждому параметру строим график и вставляем в PDF
    for key, title in [
        ("price", "Динамика цены"),
        ("discount", "Динамика скидки"),
        ("quantity", "Динамика остатков")
    ]:
        # 4.1 Подготовка данных
        dates = [h["parsed_at"] for h in history]
        values = []
        for h in history:
            v = h.get(key)
            try:
                # убираем лишние символы, конвертируем
                val = float(str(v).replace("%", "").replace(",", "."))
            except Exception:
                val = 0.0
            values.append(val)

        # 4.2 Строим график matplotlib
        fig, ax = plt.subplots(figsize=(6, 2.5))
        ax.plot(dates, values, marker="o")
        ax.set_title(title, fontname="DejaVuSans")
        ax.tick_params(axis='x', labelrotation=45)
        plt.tight_layout()

        # 4.3 Сохраняем график во временный буфер
        img_buffer = BytesIO()
        fig.savefig(img_buffer, format="PNG")
        plt.close(fig)
        img_buffer.seek(0)

        # 4.4 Вставляем в PDF
        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Image(img_buffer, width=400, height=150))
        elements.append(Spacer(1, 12))

    # 5. Генерируем и возвращаем путь
    doc.build(elements)
    return filename