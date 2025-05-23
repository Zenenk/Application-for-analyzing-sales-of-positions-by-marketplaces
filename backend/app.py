import os
import csv
import tempfile
import logging
import configparser
import urllib.parse
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
from threading import Thread
import threading
from flask import jsonify
from sqlalchemy import distinct
import glob
from datetime import datetime
from io import StringIO
from flask import Response

from backend.config_parser import read_config
from backend.database import init_db, add_product, get_products, get_product_history, SessionLocal, Product
from backend.scraper import scrape_marketplace
from backend.promo_detector import PromoDetector
from backend.exporter import export_to_csv, export_to_pdf, export_product_pdf, CSV_RESULTS, PDF_RESULTS
from backend.schedule_manager import update_schedule_interval, start_scheduler
from backend.utils.marketplace_urls import build_search_url, build_product_url

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация базы данных и планировщика
init_db()

def _background_scrape_and_save(marketplace, urls, categories, articles, limit):
    logger.info(f"🟢 [Background] _run_start kicked off: marketplace={marketplace}, urls={urls}")
    all_products = []
    for url in urls:
        logger.info(f"  → [Background] Scraping {url}")
        try:
            prods = scrape_marketplace(
                url,
                category_filter=categories or None,
                article_filter=articles   or None,
                limit=limit,
                marketplace=marketplace
            )
            logger.info(f"    ← [Background] Got {len(prods)} products from {url}")
            all_products.extend(prods)
        except Exception as e:
            logger.error(f"    ✖ [Background] Ошибка при скрапинге {url}: {e}")
    # Сохраняем в БД
    for p in all_products:
        try:
            promo_labels = p.get("promo_labels", []) or []
            promotion_detected = bool(p.get("discount") or promo_labels)
            detected_keywords = ";".join(promo_labels)

            add_product({
                "name":               p.get("name", ""),
                "article":            p.get("article", ""),
                "price":              str(p.get("price", "")),
                "quantity":           str(p.get("quantity", "")),
                "image_url":          p.get("image_url", ""),
                "marketplace":        marketplace,
                "category":           categories[0] if categories else "",
                "promotion_detected": promotion_detected,
                "detected_keywords":  detected_keywords,
                "price_old":          p.get("price_old", ""),
                "price_new":          p.get("price_new", ""),
                "discount":           p.get("discount", ""),
                "promo_labels":       ";".join(p.get("promo_labels", [])),
                "parsed_at":          p.get("parsed_at"),
            })
        except Exception as e:
            logger.error(f"Ошибка сохранения продукта {p.get('article')}: {e}")
    logger.info("🟢 [Background] Scraping and saving done.")


def _split_csv(val):
    if not val:
        return []
    if isinstance(val, list):
        return val
    return [v.strip() for v in val.split(",") if v.strip()]

def build_search_urls(marketplace: str, query_type: str, query_value: str) -> list[str]:
    """
    Возвращает список URL для парсинга по выбору маркетплейса.
    Поддерживаемые комбинации:
      - Ozon + category  →  https://www.ozon.ru/category/...&text={query}
      - Ozon + product   →  https://www.ozon.ru/product/{query}/?...
      - Wildberries + category → https://www.wildberries.ru/catalog/0/search.aspx?search={query}
      - Wildberries + product  → https://www.wildberries.ru/catalog/{query}/detail.aspx
    """
    qm = urllib.parse.quote(query_value)
    urls: list[str] = []

    if marketplace.lower() == "ozon":
        if query_type == "category":
            urls.append(
                f"https://www.ozon.ru/category/produkty-pitaniya-9200/"
                f"?category_was_predicted=true&deny_category_prediction=true"
                f"&from_global=true&text={qm}"
            )
        elif query_type == "product":
            # query_value должен быть артикул или слаг
            urls.append(
                f"https://www.ozon.ru/product/{query_value}/"
                f"?at=A6tGKG5vQcw9pWPWC99BK3cwDEQqlUw8Opm3C3YvY73"
            )

    elif marketplace.lower() in ("wildberries", "вб", "wb"):
        if query_type == "category":
            urls.append(
                f"https://www.wildberries.ru/catalog/0/search.aspx?search={qm}"
            )
        elif query_type == "product":
            # query_value — числовой ID товара
            urls.append(
                f"https://www.wildberries.ru/catalog/{query_value}/detail.aspx"
            )

    else:
        raise ValueError(f"Неподдерживаемый маркетплейс: {marketplace}")

    return urls


app = Flask(__name__)
# Разрешаем любые origin и все методы/заголовки
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@app.route("/", methods=["GET"])
def index():
    return '''
    <html>
      <body>
        <form action="/start" method="post" enctype="multipart/form-data">
          <input type="file" name="config_file"/>
          <button type="submit">Run</button>
        </form>
      </body>
    </html>
    '''

@app.route("/start", methods=["POST"])
def start():
    limit = 10
    urls = []
    categories = []
    articles = []
    save_to_db = False

    # JSON-режим: запускаем фон и сразу возвращаем 202
    if request.content_type and request.content_type.startswith("application/json"):
        data = request.get_json() or {}
        marketplace = data.get("marketplace")
        qtype       = data.get("type")
        qval        = data.get("query")
        limit       = int(data.get("limit", limit))
        if not all([marketplace, qtype, qval]):
            return jsonify({"error": "Некорректные параметры"}), 400

        if qtype == "category":
            urls       = [ build_search_url(marketplace, qval) ]
            categories = [ qval ]
        else:
            urls       = [ build_product_url(marketplace, qval) ]
            articles   = [ qval ]

        # фоновый запуск
        threading.Thread(
            target=_background_scrape_and_save,
            args=(marketplace, urls, categories, articles, limit),
            daemon=True
        ).start()

        return ("", 202)

    # Form-data режим (синхронный, с CSV/PDF)
    cfg_file = request.files.get("config_file")
    if not cfg_file:
        return jsonify({"error": "Нет файла конфигурации"}), 400
    fn = secure_filename(cfg_file.filename)
    os.makedirs("backend/config", exist_ok=True)
    path = os.path.join("backend/config", fn)
    cfg_file.save(path)

    try:
        cfg = read_config(path)
    except Exception as e:
        return jsonify({"error": f"Ошибка чтения конфигурации: {e}"}), 400

    marketplace = cfg["MARKETPLACES"]["marketplaces"]
    search_cfg  = cfg.get("SEARCH", {})

    urls       = _split_csv(search_cfg.get("urls", ""))
    categories = _split_csv(search_cfg.get("categories", ""))
    articles   = _split_csv(search_cfg.get("articles", ""))
    save_to_db = cfg.get("EXPORT", {}).get("save_to_db", "False") == "True"

    all_products = []
    for url in urls:
        try:
            prods = scrape_marketplace(
                url,
                category_filter=categories or None,
                article_filter=articles   or None,
                limit=limit,
                marketplace=marketplace
            )
            all_products.extend(prods)
        except Exception as e:
            logger.error(f"Ошибка при скрапинге {url}: {e}")

    if save_to_db:
        for p in all_products:
            # Извлекаем флаги и ключевые слова прямо из level fields
            promo_labels = p.get("promo_labels", []) or []
            promotion_detected = bool(p.get("discount") or promo_labels)
            detected_keywords = ";".join(promo_labels)

            add_product({
                "name":               p.get("name", ""),
                "article":            p.get("article", ""),
                "price":              str(p.get("price", "")),
                "quantity":           str(p.get("quantity", "")),
                "image_url":          p.get("image_url", ""),
                "marketplace":        marketplace,
                "category":           categories[0] if categories else "",
                "promotion_detected": promotion_detected,
                "detected_keywords":  detected_keywords,
                "price_old":          p.get("price_old", ""),
                "price_new":          p.get("price_new", ""),
                "discount":           p.get("discount", ""),
                "promo_labels":       detected_keywords,
                "parsed_at":          p.get("parsed_at"),
            })

    # возвращаем отчёты
    csv_file = export_to_csv(all_products)
    pdf_file = export_to_pdf(all_products)
    return jsonify({
        "products": all_products,
        "csv_file": csv_file,
        "pdf_file": pdf_file
    })

def _run_start(urls, categories, articles, limit, save_to_db, marketplace):
    """
    Собирает те же шаги, что раньше в start(): парсинг, анализ промо, BД и экспорт.
    """
    logger.info(f"🟢 [Background] _run_start kicked off: marketplace={marketplace}, urls={urls}, category={categories}")
    all_products = []
    for url in urls:
        logger.info(f"  → Scraping {url}")
        try:
            prods = scrape_marketplace(
                url,
                category_filter=categories or None,
                article_filter=articles or None,
                limit=limit,
                marketplace=marketplace
            )
            all_products.extend(prods)
        except Exception as e:
            logger.error(f"Ошибка при скрапинге {url}: {e}")
            logger.exception(f"❌ Ошибка при скрапинге {url}:")

    # 4) Сохранение в БД
    if save_to_db:
        for p in all_products:
            # Извлекаем флаги и ключевые слова прямо из level fields
            promo_labels = p.get("promo_labels", []) or []
            promotion_detected = bool(p.get("discount") or promo_labels)
            detected_keywords = ";".join(promo_labels)

            add_product({
                "name":               p.get("name", ""),
                "article":            p.get("article", ""),
                "price":              str(p.get("price", "")),
                "quantity":           str(p.get("quantity", "")),
                "image_url":          p.get("image_url", ""),
                "marketplace":        marketplace,
                "category":           categories[0] if categories else "",
                "promotion_detected": promotion_detected,
                "detected_keywords":  detected_keywords,
                "price_old":          p.get("price_old", ""),
                "price_new":          p.get("price_new", ""),
                "discount":           p.get("discount", ""),
                "promo_labels":       detected_keywords,
                "parsed_at":          p.get("parsed_at"),
            })

    # 5) Возвращаем ответ фронту
    logger.info(f"  → Exporting CSV/PDF")
    try:
        export_to_csv(all_products)
        export_to_pdf(all_products)
    except Exception as e:
        logger.exception("❌ Ошибка экспорта отчётов:")
    logger.info("✅ [Background] _run_start finished")

@app.route("/import/csv", methods=["POST"])
def import_csv_route():
    csv_file = request.files.get("file")
    if not csv_file:
        return jsonify({"error": "Нет файла CSV"}), 400

    filename = secure_filename(csv_file.filename)
    if not filename.lower().endswith(".csv"):
        return jsonify({"error": "Недопустимый тип файла, ожидается .csv"}), 400

    os.makedirs("csv_results", exist_ok=True)
    save_path = os.path.join("csv_results", filename)
    csv_file.save(save_path)

    inserted = 0
    errors = []
    with open(save_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        required = [
            "name","article","price","quantity", "marketplace", "category",
            "price_old","price_new","discount","promo_labels",
            "promotion_detected","detected_keywords","parsed_at"
        ]
        missing = [col for col in required if col not in reader.fieldnames]
        if missing:
            return jsonify({"error": f"Отсутствуют колонки: {missing}"}), 400

        for idx, row in enumerate(reader, start=1):
            try:
                data = {
                    "name": row["name"],
                    "article": row["article"],
                    "price": row["price"],
                    "quantity": row["quantity"],
                    "image_url": row.get("image_url", ""),
                    "promotion_detected": row["promotion_detected"].lower() in ("true","1","yes"),
                    "detected_keywords": row["detected_keywords"],
                    "price_old": row["price_old"],
                    "price_new": row["price_new"],
                    "discount": row["discount"],
                    "promo_labels": row["promo_labels"],
                    "parsed_at": row["parsed_at"],
                }
                add_product(data)
                inserted += 1
            except Exception as e:
                errors.append({"line": idx, "error": str(e)})

    return jsonify({"inserted": inserted, "errors": errors})

@app.route("/products", methods=["GET"])
def products_route():
    prods = get_products()
    output = []
    for p in prods:
        output.append({
            "id": p.id,
            "name": p.name,
            "article": p.article,
            "price": p.price,
            "quantity": p.quantity,
            "image_url": p.image_url,
            "marketplace": p.marketplace,
            "category":    p.category,
            "promotion_detected": p.promotion_detected,
            "detected_keywords": p.detected_keywords.split(";") if p.detected_keywords else [],
            "price_old": p.price_old,
            "price_new": p.price_new,
            "discount": p.discount,
            "promo_labels": p.promo_labels.split(";") if p.promo_labels else [],
            "parsed_at": p.parsed_at.isoformat() if p.parsed_at else None,
            "timestamp": p.timestamp.isoformat(),
        })
    return jsonify(output)

# Список уникальных категорий из БД
@app.route("/categories", methods=["GET"])
def categories_route():
    session = SessionLocal()
    try:
        # всё, что не пустая строка и не None
        cats = (
            session.query(distinct(Product.category))
            .filter(Product.category != None, Product.category != "")
            .order_by(Product.category)
            .all()
        )
        return jsonify([c[0] for c in cats])
    finally:
        session.close()

@app.route("/marketplaces", methods=["GET"])
def marketplaces_route():
    session = SessionLocal()
    try:
        mps = (
            session.query(distinct(Product.marketplace))
            .filter(Product.marketplace != None, Product.marketplace != "")
            .order_by(Product.marketplace)
            .all()
        )
        return jsonify([m[0] for m in mps])
    finally:
        session.close()

@app.route("/products/history/<string:article>", methods=["GET"])
def product_history(article):
    try:
        history = get_product_history(article)
        if not history:
            return jsonify({"error": "История не найдена"}), 404
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error getting history for {article}: {e}")
        return jsonify({"error": "Внутренняя ошибка"}), 500


@app.route("/dashboard", methods=["GET"])
def dashboard_route():
    products = get_products()
    count = len(products)
    last_compare = {}
    if count >= 2:
        sorted_prods = sorted(products, key=lambda p: p.timestamp)
        old, new = sorted_prods[-2], sorted_prods[-1]
        try:
            price_diff = float(new.price) - float(old.price)
        except Exception:
            price_diff = None
        try:
            qty_diff = int(new.quantity) - int(old.quantity)
        except Exception:
            qty_diff = None
        last_compare = {"price_diff": price_diff, "quantity_diff": qty_diff}
    return jsonify({"products_count": count, "last_compare": last_compare})

@app.route("/reports", methods=["GET"])
def reports_route():
    reports = []
    csv_dir = "csv_results"
    if os.path.isdir(csv_dir):
        files = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]
        if files:
            reports.append({"id": "csv", "title": "CSV отчёт"})
    pdf_dir = "pdf_results"
    if os.path.isdir(pdf_dir):
        files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
        if files:
            reports.append({"id": "pdf", "title": "PDF отчёт"})
    return jsonify(reports)

@app.route("/export/product/<string:article>", methods=["GET"])
def export_product_report(article):
    try:
        # Генерируем имя файла в нужном формате
        today = datetime.now().strftime("%d_%m_%Y")
        filename = f"товар_{article}_{today}.pdf"
        filepath = os.path.join(PDF_RESULTS, filename)

        # Если файла ещё нет — создаём его
        if not os.path.isfile(filepath):
            filepath = export_product_pdf(article, path=filepath)

        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype="application/pdf"
        )
    except FileNotFoundError:
        # если истории на самом деле нет
        abort(404, description="История товара не найдена")
    except Exception as e:
        app.logger.error(f"Error exporting product PDF {article}: {e}", exc_info=True)
        abort(500, description="Ошибка формирования отчёта")


@app.route("/download/<kind>", methods=["GET"])
def download_report(kind):
    """
    kind = 'csv' или 'pdf' — отдает самый свежий файл из папок csv_results/pdf_results
    """
    if kind not in ("csv", "pdf"):
        abort(404)
    folder = CSV_RESULTS if kind == "csv" else PDF_RESULTS
    pattern = os.path.join(folder, f"*.{kind}")
    files = glob.glob(pattern)
    if not files:
        abort(404, description=f"No {kind.upper()} reports yet")
    latest = sorted(files)[-1]
    mime = "text/csv" if kind == "csv" else "application/pdf"
    return send_file(
        latest,
        as_attachment=True,
        download_name=os.path.basename(latest),
        mimetype=mime
    )


@app.route("/export/csv", methods=["GET"])
def export_csv_from_db():
    prods = get_products()  # ORM-модели Product
    # Подготовим in-memory CSV
    si = StringIO()
    fieldnames = [
        "id", "name", "article", "price", "quantity", "image_url",
        "price_old", "price_new", "discount", "promo_labels",
        "promotion_detected", "detected_keywords", "parsed_at", "timestamp"
    ]
    writer = csv.DictWriter(si, fieldnames=fieldnames)
    writer.writeheader()
    for p in prods:
        writer.writerow({
            "id": p.id,
            "name": p.name,
            "article": p.article,
            "price": p.price,
            "quantity": p.quantity,
            "image_url": p.image_url,
            "price_old": p.price_old,
            "price_new": p.price_new,
            "discount": p.discount,
            "promo_labels": p.promo_labels or "",
            "promotion_detected": p.promotion_detected,
            "detected_keywords": p.detected_keywords or "",
            "parsed_at": p.parsed_at.isoformat() if p.parsed_at else "",
            "timestamp": p.timestamp.isoformat()
        })
    output = si.getvalue().encode("utf-8-sig")
    si.close()

    return Response(
        output,
        mimetype="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment;filename=products_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@app.route("/export/pdf", methods=["GET"])
def export_pdf_from_db():
    prods = [ 
        { 
          "name": p.name,
          "article": p.article,
          # ... остальные поля ...
          "parsed_at": p.parsed_at.isoformat() if p.parsed_at else ""
        }
        for p in get_products()
    ]
    # воспользуемся вашей функцией export_to_pdf, но передав path=None
    pdf_path = export_to_pdf(prods, path=None)
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=os.path.basename(pdf_path),
        mimetype="application/pdf"
    )


# Обновление интервала выполнения фоновых задач
@app.route("/schedule", methods=["POST"])
def set_schedule():
    interval = int(request.json.get("interval", 1))
    update_schedule_interval(interval)
    return jsonify({"interval": interval})

if __name__ == "__main__":
    # Запуск планировщика и сервера
    start_scheduler()
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=(os.getenv("FLASK_DEBUG", "False").lower() in ("true", "1")))
