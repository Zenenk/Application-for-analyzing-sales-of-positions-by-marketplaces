# exporter.py

import os
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Пути к директориям
BACKEND_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(BACKEND_DIR, os.pardir))
PDF_DIR = os.path.join(PROJECT_ROOT, "pdf_results")
CSV_DIR = os.path.join(PROJECT_ROOT, "csv_results")
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs(CSV_DIR, exist_ok=True)

# Регистрируем кириллический шрифт
FONT_FILENAME = os.path.join(BACKEND_DIR, "DejaVuSans.ttf")
pdfmetrics.registerFont(TTFont("DejaVuSans", FONT_FILENAME))

# Стили
base_style = ParagraphStyle(
    name="BaseStyle",
    fontName="DejaVuSans",
    fontSize=9,
    leading=11,
    wordWrap="CJK"
)
small_style = ParagraphStyle(
    name="SmallStyle",
    fontName="DejaVuSans",
    fontSize=7,
    leading=8,
    alignment=1,
    wordWrap="CJK"
)

def _make_timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

def export_to_pdf(products: list[dict], path: str | None = None):
    if path is None:
        filename = f"report_{_make_timestamp()}.pdf"
        path = os.path.join(PDF_DIR, filename)

    page_w, _ = A4
    margin = 10 * mm
    usable_w = page_w - 2 * margin

    doc = SimpleDocTemplate(
        path,
        pagesize=A4,
        leftMargin=margin, rightMargin=margin,
        topMargin=15*mm, bottomMargin=15*mm
    )

    story = [
        Paragraph("Отчет по товарам", ParagraphStyle(
            name="Title", fontName="DejaVuSans", fontSize=16, leading=18
        )),
        Spacer(1, 5*mm)
    ]

    data = [["Name","Article","Price","Qty","Promo","Keywords","ParsedAt"]]
    for p in products:
        ts = p.get("parsed_at", datetime.now(timezone.utc))
        ts_text = ts.strftime("%Y-%m-%d\n%H:%M:%S")
        promo = p.get("promotion", {})
        keywords = promo.get("detected_keywords", [])
        data.append([
            Paragraph(p.get("name",""), base_style),
            Paragraph(str(p.get("article","")), small_style),  # использует small_style
            str(p.get("price","")),
            str(p.get("quantity","")),
            str(promo.get("promotion_detected", False)),
            Paragraph(", ".join(keywords), base_style),
            Paragraph(ts_text, small_style),
        ])

    ratios = [2,1,1,1,1,2,1]
    total = sum(ratios)
    colWidths = [usable_w * r/total for r in ratios]

    table = Table(data, colWidths=colWidths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("GRID",           (0,0),(-1,-1),0.4,colors.grey),
        ("BACKGROUND",     (0,0),(-1,0),colors.HexColor("#B3DDF2")),
        ("TEXTCOLOR",      (0,0),(-1,0),colors.black),
        ("ALIGN",          (2,1),(3,-1),"RIGHT"),
        ("VALIGN",         (0,0),(-1,-1),"MIDDLE"),
        ("FONTNAME",       (0,0),(-1,-1),"DejaVuSans"),
        ("FONTSIZE",       (0,0),(-1,0),9),    # шапка
        ("FONTSIZE",       (1,1),(1,-1),7),    # Article — мелкий 7pt
        ("FONTSIZE",       (6,1),(6,-1),7),    # ParsedAt — мелкий 7pt
        ("BOTTOMPADDING",  (0,0),(-1,0),6),
    ]))

    story.append(table)
    doc.build(story)
    print(f"📄 PDF сохранён: {path}")

def export_to_csv(products: list[dict], path: str | None = None):
    import csv
    if path is None:
        filename = f"report_{_make_timestamp()}.csv"
        path = os.path.join(CSV_DIR, filename)

    fieldnames = [
        "name","article","price","quantity",
        "promotion_detected","detected_keywords","parsed_at"
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for p in products:
            ts = p.get("parsed_at", datetime.now(timezone.utc))
            promo = p.get("promotion", {})
            writer.writerow({
                "name":               p.get("name",""),
                "article":            p.get("article",""),
                "price":              p.get("price",""),
                "quantity":           p.get("quantity",""),
                "promotion_detected": promo.get("promotion_detected", False),
                "detected_keywords":  ";".join(promo.get("detected_keywords", [])),
                "parsed_at":          ts.isoformat(),
            })
    print(f"📑 CSV сохранён: {path}")
