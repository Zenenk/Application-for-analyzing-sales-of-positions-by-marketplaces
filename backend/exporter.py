import csv
from datetime import datetime
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

def export_to_pdf(products: list[dict], path: str):
    """
    Генерирует PDF с табличкой:
    колонка Name, Article, Price, Quantity, Promo (True/False), Keywords, ParsedAt
    """
    c = canvas.Canvas(path, pagesize=LETTER)
    width, height = LETTER

    # Заголовок
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, height - 20 * mm, "Отчет по товарам")
    c.setFont("Helvetica", 10)

    # Шапка таблицы
    y = height - 30 * mm
    headers = ["Name", "Article", "Price", "Qty", "Promo", "Keywords", "ParsedAt"]
    col_widths = [50*mm, 25*mm, 20*mm, 15*mm, 15*mm, 50*mm, 30*mm]
    x_positions = [20*mm]
    for w in col_widths[:-1]:
        x_positions.append(x_positions[-1] + w)

    for i, h in enumerate(headers):
        c.drawString(x_positions[i], y, h)
    y -= 8 * mm

    # Строки
    for p in products:
        # Если нет parsed_at, подставим сейчас
        ts = p.get("parsed_at", datetime.utcnow())
        line = [
            str(p.get("name","")),
            str(p.get("article","")),
            str(p.get("price","")),
            str(p.get("quantity","")),
            str(p.get("promotion", {}).get("promotion_detected", False)),
            ", ".join(p.get("promotion",{}).get("detected_keywords", [])),
            ts.isoformat() if isinstance(ts, datetime) else str(ts),
        ]
        for i, text in enumerate(line):
            # Уменьшаем размер шрифта, если текст длинный
            c.setFont("Helvetica", 8 if len(text) > 20 else 10)
            c.drawString(x_positions[i], y, text[: int(col_widths[i] / (3.5*mm)) ])
        y -= 6 * mm
        if y < 20 * mm:
            c.showPage()
            y = height - 20 * mm

    c.save()


def export_to_csv(products: list[dict], path: str):
    """
    Генерирует CSV с теми же колонками, что и PDF.
    """
    fieldnames = [
        "name", "article", "price", "quantity",
        "promotion_detected", "detected_keywords", "parsed_at"
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            ts = p.get("parsed_at", datetime.utcnow())
            writer.writerow({
                "name": p.get("name",""),
                "article": p.get("article",""),
                "price": p.get("price",""),
                "quantity": p.get("quantity",""),
                "promotion_detected": p.get("promotion",{}).get("promotion_detected", False),
                "detected_keywords": ";".join(p.get("promotion",{}).get("detected_keywords", [])),
                "parsed_at": ts.isoformat() if isinstance(ts, datetime) else str(ts)
            })
