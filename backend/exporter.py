import os
import csv
import requests
from io import BytesIO
from datetime import datetime
from zoneinfo import ZoneInfo

import matplotlib.dates as mdates
from sqlalchemy import desc
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Image,
    Spacer,
    SimpleDocTemplate,
)

from backend.database import SessionLocal, Product, get_product_history

# --- Папки для отчётов ---
CSV_RESULTS = "/app/csv_results"
PDF_RESULTS = "/app/pdf_results"
os.makedirs(CSV_RESULTS, exist_ok=True)
os.makedirs(PDF_RESULTS, exist_ok=True)

# --- Регистрация шрифта для кириллицы ---
DEJAVU_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
if not os.path.isfile(DEJAVU_PATH):
    raise RuntimeError(f"Не найден шрифт DejaVuSans по пути {DEJAVU_PATH}")
pdfmetrics.registerFont(TTFont("DejaVuSans", DEJAVU_PATH))


def export_to_csv(products: list[dict], path: str | None = None) -> str:
    """
    Экспортирует список продуктов в CSV.
    Возвращает путь к файлу.
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = path or os.path.join(CSV_RESULTS, f"report_{ts}.csv")

    fieldnames = [
        "name",
        "article",
        "price",
        "quantity",
        "image_url",
        "price_old",
        "price_new",
        "discount",
        "promo_labels",
        "promotion_detected",
        "detected_keywords",
        "parsed_at",
    ]

    with open(filename, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            labels = p.get("promo_labels") or []
            writer.writerow({
                "name":                p.get("name", ""),
                "article":             p.get("article", ""),
                "price":               p.get("price", ""),
                "quantity":            p.get("quantity", ""),
                "image_url":           p.get("image_url", ""),
                "price_old":           p.get("price_old", ""),
                "price_new":           p.get("price_new", ""),
                "discount":            p.get("discount", ""),
                "promo_labels":        ";".join(labels),
                "promotion_detected":  p.get("promotion_analysis", {}).get("promotion_detected", False),
                "detected_keywords":   ";".join(p.get("promotion_analysis", {}).get("detected_keywords", [])),
                "parsed_at":           p.get("parsed_at", datetime.now().isoformat()),
            })
    return filename


def export_to_pdf(products: list[dict], path: str | None = None) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = path or os.path.join(PDF_RESULTS, f"report_{ts}.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=0.5*mm,
        rightMargin=0.5*mm,
        topMargin=12*mm,
        bottomMargin=12*mm,
    )
    elements: list = []

    styles = getSampleStyleSheet()
    for name in ("Normal","Title","Heading1","Heading2"):
        styles[name].fontName = "DejaVuSans"

    # стиль для обёртки текста в ячейках
    wrap = ParagraphStyle(
        name="wrap",
        parent=styles["Normal"],
        leading=10,
        wordWrap="CJK"
    )

    # Заголовок
    elements.append(Paragraph("Список товаров", styles["Title"]))
    elements.append(Spacer(1, 12))

    # Время формирования отчёта по МСК
    msk_now = datetime.now(ZoneInfo("Europe/Moscow")).strftime("%d.%m.%Y %H:%M:%S МСК")
    elements.append(Paragraph(f"Отчёт сформирован: {msk_now}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    header = [
        "Name","Article","Price","Quantity",
        "Old Price","New Price","Discount",
        "Promo Labels","Promo Detected","Keywords","Parsed At"
    ]
    data = [[Paragraph(h, styles["Heading2"]) for h in header]]

    for p in products:
        row = [
            Paragraph(str(p.get("name","")), wrap),
            Paragraph(str(p.get("article","")), wrap),
            Paragraph(str(p.get("price","")), wrap),
            Paragraph(str(p.get("quantity","")), wrap),
            Paragraph(str(p.get("price_old","")), wrap),
            Paragraph(str(p.get("price_new","")), wrap),
            Paragraph(str(p.get("discount","")), wrap),
            Paragraph(", ".join(p.get("promo_labels",[])), wrap),
            Paragraph(str(p.get("promotion_detected", False)), wrap),
            Paragraph(", ".join(p.get("detected_keywords",[])), wrap),
            Paragraph(str(p.get("parsed_at","")), wrap),
        ]
        data.append(row)

    # все колонки равной ширины
    col_count = len(header)
    col_widths = [doc.width/col_count]*col_count

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("TEXTCOLOR",   (0,0), (-1,0), colors.black),
        ("ALIGN",       (0,0), (-1,-1), "LEFT"),
        ("VALIGN",      (0,0), (-1,-1), "TOP"),
        ("GRID",        (0,0), (-1,-1), 0.5, colors.grey),
    ]))

    elements.append(table)
    doc.build(elements)
    return filename


def export_product_pdf(article: str, path: str | None = None) -> str:
    """
    Формирует PDF-отчёт с карточкой товара и графиками.
    Название, категория, маркетплейс и изображение берутся из последней записи в БД.
    """
    # 1) Получаем историю и сам товар из БД
    history = get_product_history(article)
    session = SessionLocal()
    prod = (
        session.query(Product)
        .filter(Product.article == article)
        .order_by(desc(Product.parsed_at), desc(Product.timestamp))
        .first()
    )
    session.close()

    # 2) Подготовка имени файла
    date_for_name = datetime.now().strftime("%d_%m_%Y")
    filename = path or os.path.join(PDF_RESULTS, f"товар_{article}_{date_for_name}.pdf")

    # 3) Создаем документ
    doc = SimpleDocTemplate(filename, pagesize=letter)
    elements: list = []

    styles = getSampleStyleSheet()
    for st in ("Normal", "Title", "Heading1", "Heading2"):
        styles[st].fontName = "DejaVuSans"

    # 4) Заголовок — название товара из БД (или fallback)
    name = prod.name if prod and prod.name else f"Товар {article}"
    elements.append(Paragraph(name, styles["Heading1"]))
    elements.append(Spacer(1, 8))

    # 5) Изображение из БД (или из истории, если надо)
    img_url = prod.image_url if prod and prod.image_url else (history[-1].get("image_url") if history else None)
    if img_url:
        try:
            resp = requests.get(img_url, timeout=10)
            buf = BytesIO(resp.content)
            elements.append(Image(buf, width=200, height=200))
            elements.append(Spacer(1, 8))
        except Exception:
            pass

    # 6) Артикул, категория, маркетплейс
    elements.append(Paragraph(f"Артикул: {article}", styles["Normal"]))
    if prod and prod.category:
        elements.append(Paragraph(f"Категория: {prod.category}", styles["Normal"]))
    if prod and prod.marketplace:
        elements.append(Paragraph(f"Маркетплейс: {prod.marketplace}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # 7) Старые/новые цены и скидка
    last = history[-1] if history else {}
    if last.get("price_old"):
        elements.append(Paragraph(f"Старая цена: {last['price_old']}", styles["Normal"]))
    if last.get("price_new"):
        elements.append(Paragraph(f"Новая цена: {last['price_new']}", styles["Normal"]))
    if last.get("discount"):
        elements.append(Paragraph(f"Скидка: {last['discount']}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    # 8) Графики по истории
    for key, title in [
        ("price", "Динамика цены"),
        ("discount", "Динамика скидки"),
        ("quantity", "Динамика остатков")
    ]:
        # собираем даты и значения
        dates_iso = [h["parsed_at"] for h in history]
        dates = [datetime.fromisoformat(d) for d in dates_iso]
        vals = []
        for h in history:
            try:
                v = float(str(h.get(key)).replace("%", "").replace(",", "."))
            except Exception:
                v = 0.0
            vals.append(v)

        # строим график
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.plot(dates, vals, marker="o")
        ax.set_title(title, fontname="DejaVuSans")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m.%Y"))
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        fig.autofmt_xdate(rotation=45)
        ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.5)

        buf = BytesIO()
        fig.savefig(buf, format="PNG", dpi=150)
        plt.close(fig)
        buf.seek(0)

        elements.append(Paragraph(title, styles["Heading2"]))
        elements.append(Image(buf, width=400, height=200))
        elements.append(Spacer(1, 12))

    # 9) Сборка PDF
    doc.build(elements)
    return filename
