# backend/app.py
import os
import csv
import tempfile
import logging
import configparser
from flask import Flask, request, jsonify, send_file, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename

from backend.config_parser import read_config
from backend.database import init_db, add_product, get_products, get_product_history
from backend.scraper import scrape_marketplace
from backend.promo_detector import PromoDetector
from backend.exporter import export_to_csv, export_to_pdf, export_product_pdf
from backend.screenshot_importer import import_from_screenshot
from backend.schedule_manager import start_scheduler

start_scheduler()


app = Flask(__name__)
CORS(app)
init_db()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    config_path = None

    # Поддержка JSON-запроса из frontend
    if request.content_type.startswith("application/json"):
        data = request.get_json()
        marketplace = data.get("marketplace")
        query_type = data.get("type")
        query_value = data.get("query")
        limit = int(data.get("limit", 10))

        if not all([marketplace, query_type, query_value]):
            return jsonify({"error": "Некорректные параметры"}), 400

        # Генерация временного INI-конфига
        config = configparser.ConfigParser()
        config["MARKETPLACES"] = {"marketplaces": marketplace}
        config["SEARCH"] = {
            "urls": "",
            "categories": query_value if query_type == "category" else "",
            "articles": query_value if query_type == "product" else "",
        }
        config["EXPORT"] = {"save_to_db": "True"}

        tmpfile = tempfile.NamedTemporaryFile(delete=False, suffix=".conf")
        config.write(tmpfile)
        tmpfile.close()
        config_path = tmpfile.name

    else:
        # Загрузка конфигурации из файла
        config_file = request.files.get("config_file")
        if not config_file:
            return jsonify({"error": "Нет файла конфигурации"}), 400

        filename = secure_filename(config_file.filename)
        config_path = os.path.join("backend", "config", filename)
        config_file.save(config_path)

    # Чтение и парсинг конфига
    try:
        config = read_config(config_path)
    except Exception as e:
        return jsonify({"error": f"Ошибка чтения конфигурации: {e}"}), 400

    urls = config.get("SEARCH", {}).get("urls", "").split(",")
    categories = config.get("SEARCH", {}).get("categories", "").split(",")
    articles = config.get("SEARCH", {}).get("articles", "").split(",")
    save_to_db = config.get("EXPORT", {}).get("save_to_db", "False") == "True"

    all_products = []
    # Скрапинг по каждому URL
    for url in urls:
        if not url.strip():
            continue
        try:
            prods = scrape_marketplace(
                url.strip(),
                category_filter=categories,
                article_filter=articles,
                limit=limit
            )
            all_products.extend(prods)
        except Exception as e:
            logger.error(f"Ошибка при скрапинге {url}: {e}")

    # Анализ промо-картинок
    promo = PromoDetector()
    for p in all_products:
        img = p.get("image_url")
        if not img:
            p["promotion_analysis"] = {
                "promotion_detected": False,
                "detected_keywords": [],
                "ocr_text": "",
                "promotion_probability": 0.0
            }
            continue
        try:
            res = promo.predict_promotion(img)
            p["promotion_analysis"] = res
        except Exception as e:
            p["promotion_analysis"] = {
                "promotion_detected": False,
                "detected_keywords": [],
                "ocr_text": str(e),
                "promotion_probability": 0.0
            }

    # Сохранение в БД
    for p in all_products:
        if save_to_db:
            product_data = {
                "name": p.get("name", ""),
                "article": p.get("article", ""),
                "price": str(p.get("price", "")),
                "quantity": str(p.get("quantity", "")),
                "image_url": p.get("image_url", ""),
                "marketplace": p.get("marketplace", ""),
                "category":    p.get("category", ""),
                "promotion_detected": p.get("promotion_analysis", {}).get("promotion_detected", False),
                "detected_keywords": ";".join(p.get("promotion_analysis", {}).get("detected_keywords", [])),
                "price_old": p.get("price_old", ""),
                "price_new": p.get("price_new", ""),
                "discount": p.get("discount", ""),
                "promo_labels": ";".join(p.get("promo_labels", [])),
            }
            add_product(product_data)

    # Генерация отчётов
    csv_file = export_to_csv(all_products)
    pdf_file = export_to_pdf(all_products)

    return jsonify({
        "products": all_products,
        "csv_file": csv_file,
        "pdf_file": pdf_file
    })

@app.route("/import/csv", methods=["POST"])
def import_csv_route():
    # Получаем файл и проверяем
    csv_file = request.files.get("file")
    if not csv_file:
        return jsonify({"error": "Нет файла CSV"}), 400

    filename = secure_filename(csv_file.filename)
    if not filename.lower().endswith(".csv"):
        return jsonify({"error": "Недопустимый тип файла, ожидается .csv"}), 400

    # Сохраняем во временную директорию
    os.makedirs("csv_results", exist_ok=True)
    save_path = os.path.join("csv_results", filename)
    csv_file.save(save_path)

    inserted = 0
    errors = []
    with open(save_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        # Ожидаемые колонки
        required = [
            "name","article","price","quantity",
            "price_old","price_new","discount","promo_labels",
            "promotion_detected","detected_keywords","parsed_at"
        ]
        missing = [col for col in required if col not in reader.fieldnames]
        if missing:
            return jsonify({"error": f"Отсутствуют колонки: {missing}"}), 400

        for idx, row in enumerate(reader, start=1):
            try:
                # Подготавливаем словарь для add_product
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
            "promotion_detected": p.promotion_detected,
            "detected_keywords": p.detected_keywords.split(";") if p.detected_keywords else [],
            "marketplace": p.marketplace,
            "category":    p.category,
            "price_old": p.price_old,
            "price_new": p.price_new,
            "discount": p.discount,
            "promo_labels": p.promo_labels.split(";") if p.promo_labels else [],
            "parsed_at": p.parsed_at.isoformat() if p.parsed_at else None,
            "timestamp": p.timestamp.isoformat(),
        })
    return jsonify(output)

@app.route("/products/history/<string:article>", methods=["GET"])
def product_history(article):
    """
    Возвращает JSON-массив с историей изменений по данному артикулу.
    """
    try:
        history = get_product_history(article)
        if not history:
            return jsonify({"error": "История не найдена"}), 404
        return jsonify(history)
    except Exception as e:
        logger.error(f"Error getting history for {article}: {e}")
        return jsonify({"error": "Внутренняя ошибка"}), 500
    

@app.route("/export/product/<string:article>", methods=["GET"])
def export_product_report(article):
    """
    Экспорт PDF с графиками по товару article.
    """
    try:
        filepath = export_product_pdf(article)
        # download_name — имя файла, отправляемое клиенту
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath),
            mimetype="application/pdf"
        )
    except FileNotFoundError:
        abort(404, description="История товара не найдена")
    except Exception as e:
        logger.error(f"Error exporting product PDF {article}: {e}")
        abort(500, description="Ошибка формирования отчёта")
        

@app.route("/dashboard", methods=["GET"])
def dashboard_route():
    """
    Возвращает обобщённые метрики:
      - products_count: общее число записей в БД
      - last_compare: разница цены и остатков между двумя последними записями
    """
    products = get_products()
    count = len(products)

    last_compare = {}
    # если хотя бы две записи — считаем разницу
    if count >= 2:
        # сортируем по timestamp (возрастающему)
        sorted_prods = sorted(products, key=lambda p: p.timestamp)
        old = sorted_prods[-2]
        new = sorted_prods[-1]
        try:
            price_diff = float(new.price) - float(old.price)
        except Exception:
            price_diff = None
        try:
            qty_diff = int(new.quantity) - int(old.quantity)
        except Exception:
            qty_diff = None
        last_compare = {
            "price_diff": price_diff,
            "quantity_diff": qty_diff
        }

    return jsonify({
        "products_count": count,
        "last_compare": last_compare
    })


@app.route("/reports", methods=["GET"])
def reports_route():
    """
    Возвращает список доступных отчётов:
      каждая запись имеет id ('csv' или 'pdf') и title
    """
    reports = []
    # ищем CSV
    csv_dir = "csv_results"
    if os.path.isdir(csv_dir):
        files = [f for f in os.listdir(csv_dir) if f.endswith(".csv")]
        if files:
            reports.append({"id": "csv", "title": "CSV отчёт"})
    # ищем PDF
    pdf_dir = "pdf_results"
    if os.path.isdir(pdf_dir):
        files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
        if files:
            reports.append({"id": "pdf", "title": "PDF отчёт"})

    return jsonify(reports)


@app.route("/download/<kind>", methods=["GET"])
def download_route(kind):
    """
    Отдаёт последний сгенерированный отчёт:
      kind = 'csv' или 'pdf'
    """
    if kind not in ("csv", "pdf"):
        abort(400, description="Недопустимый формат: ожидается csv или pdf")

    dir_map = {"csv": "csv_results", "pdf": "pdf_results"}
    directory = dir_map[kind]

    if not os.path.isdir(directory):
        abort(404, description="Каталог отчётов не найден")

    files = [f for f in os.listdir(directory) if f.endswith(f".{kind}")]
    if not files:
        abort(404, description="Отчёты не найдены")

    # Выбираем самый свежий по имени (или вы можете сортировать по дате файловой системы)
    latest = sorted(files)[-1]
    path = os.path.join(directory, latest)
    return send_file(
        path,
        as_attachment=True,
        download_name=latest,
        mimetype=f"application/{'csv' if kind=='csv' else 'pdf'}"
    )

@app.route("/import/screenshot", methods=["POST"])
def import_screenshot_route():
    # Загружаем файл и маркетплейс из form-data
    image = request.files.get("image")
    marketplace = request.form.get("marketplace")
    if not image or not marketplace:
        return jsonify({"error": "Нужны поля image и marketplace"}), 400

    # Сохраняем файл во временную папку uploads/
    os.makedirs("uploads", exist_ok=True)
    filename = secure_filename(image.filename)
    tmp_path = os.path.join("uploads", filename)
    image.save(tmp_path)

    try:
        # Вызываем утилиту, которая распознаёт и сохраняет в БД
        import_from_screenshot(tmp_path, marketplace.lower())
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/schedule", methods=["POST"])
def set_schedule():
    interval = int(request.json.get("interval", 1))
    from backend.schedule_manager import update_schedule_interval
    update_schedule_interval(interval)
    return jsonify({"interval": interval})

if __name__ == "__main__":
    from backend.schedule_manager import start_scheduler
    start_scheduler()
    app.run(host="0.0.0.0", port=5000, debug=True)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
