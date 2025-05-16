# backend/app.py
import os
import tempfile
import logging
import configparser
from flask import Flask, request, jsonify, send_file, send_file, abort
from flask_cors import CORS
from werkzeug.utils import secure_filename
from backend.config_parser import read_config
from backend.database import init_db, add_product, get_products
from backend.scraper import scrape_marketplace
from backend.promo_detector import PromoDetector
from backend.exporter import export_to_csv, export_to_pdf, export_product_pdf
from backend.database import get_product_history

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
def import_csv():
    from backend.app import import_csv
    return import_csv()

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
            # Новые поля
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
def dashboard():
    from backend.app import dashboard  # noqa: F401
    return dashboard()

@app.route("/reports", methods=["GET"])
def reports():
    from backend.app import reports  # noqa: F401
    return reports()

@app.route("/download/<kind>", methods=["GET"])
def download(kind):
    from backend.app import download  # noqa: F401
    return download(kind)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
