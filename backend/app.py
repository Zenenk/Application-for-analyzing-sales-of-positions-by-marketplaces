# backend/app.py

from flask import Flask, request, jsonify, send_file
import os
from loguru import logger
import csv
from flask_cors import CORS
from werkzeug.utils import secure_filename
from datetime import datetime

import backend.config_parser as config_parser
from backend.database import init_db, add_product, get_products
from backend.exporter import export_to_csv, export_to_pdf
from backend.analysis import compare_product_data
from backend.promo_detector import PromoDetector
import backend.scraper as scraper  # теперь с Playwright

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# Разрешаем CORS
origins = os.getenv('ALLOWED_ORIGIN', '*')
CORS(app, resources={r"/*": {"origins": origins}})

# Инициализация БД
init_db()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200

@app.route('/', methods=['GET'])
def index():
    return """
    <h1>Приложение для анализа маркетплейсов</h1>
    <form action="/start" method="post" enctype="multipart/form-data">
      <input type="file" name="config_file" />
      <input type="text"  name="save_html"  placeholder="dump.html (optional)" />
      <button type="submit">Начать анализ</button>
    </form>
    """

# Папка для импорта CSV
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CSV_UPLOADS  = os.path.join(PROJECT_ROOT, "csv_results")
os.makedirs(CSV_UPLOADS, exist_ok=True)

ALLOWED_EXTENSIONS = {"csv"}
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/import/csv", methods=["POST"])
def import_csv():
    # 1) Проверяем файл
    if "file" not in request.files:
        return jsonify({"error": "Нет части form-data с файлом"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "Не указано имя файла"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "Можно загружать только .csv"}), 400

    # 2) Сохраняем на диск
    filename = secure_filename(file.filename)
    filepath = os.path.join(CSV_UPLOADS, filename)
    file.save(filepath)

    # 3) Читаем и валидируем
    inserted = 0
    errors = []
    # теперь требуем полный шаблон
    required = {
        "name", "article", "price", "quantity",
        "promotion_detected", "detected_keywords", "parsed_at"
    }

    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        headers = set(reader.fieldnames or [])
        if not required.issubset(headers):
            missing = required - headers
            return jsonify({"error": f"Отсутствуют колонки: {', '.join(missing)}"}), 400

        for idx, row in enumerate(reader, start=2):
            try:
                name    = row["name"].strip()
                article = row["article"].strip()
                price   = float(row["price"].strip().replace(",", "."))
                quantity= int(row["quantity"].strip())
            except Exception:
                errors.append(f"Строка {idx}: неверный price или quantity")
                continue

            # promotion_detected → bool
            pd_raw = row["promotion_detected"].strip().lower()
            promo_flag = pd_raw in ("1", "true", "yes")

            # detected_keywords
            keywords = row["detected_keywords"].strip()

            # parsed_at -> datetime
            try:
                parsed_at = datetime.fromisoformat(row["parsed_at"].strip())
            except Exception:
                errors.append(f"Строка {idx}: неверный parsed_at (ожидается ISO)")
                continue

            # image_url опционально
            image_url = row.get("image_url", "").strip() or None

            data = {
                "name":               name,
                "article":            article,
                "price":              price,
                "quantity":           quantity,
                "image_url":          image_url,
                "promotion_detected": promo_flag,
                "detected_keywords":  keywords,
                "parsed_at":          parsed_at,
            }

            try:
                add_product(data)
                inserted += 1
            except Exception as e:
                errors.append(f"Строка {idx}: ошибка БД: {e}")

    return jsonify({
        "inserted": inserted,
        "errors":   errors,
        "file":     filename
    }), 200

@app.route('/start', methods=['POST'])
def start_analysis():
    file = request.files.get('config_file')
    if not file:
        return jsonify({"error": "Нет файла конфигурации"}), 400
    path = os.path.join('config', secure_filename(file.filename))
    file.save(path)
    try:
        settings = config_parser.read_config(path)
    except Exception as e:
        return jsonify({"error": f"Ошибка парсинга конфига: {e}"}), 400

    urls = settings.get('SEARCH', {}).get('urls', '')
    cats = [c.strip() for c in settings.get('SEARCH', {}).get('categories','').split(',') if c.strip()]
    save_html = request.form.get('save_html') or None

    all_products = []
    for u in urls.split(','):
        u = u.strip()
        if not u:
            continue
        try:
            logger.info(f"🔍 Начинаем парсинг URL: {u} (dump: {save_html})")
            prods = scraper.scrape_marketplace(u, category_filter=cats, limit=10, save_html=save_html)
            if settings.get('EXPORT', {}).get('save_to_db', 'false').lower() == 'true':
                for p in prods:
                    add_product(p)
            all_products.extend(prods)
        except Exception as e:
            logger.error(f"Ошибка при скрапинге {u}: {e}")
            continue

    # … promo-анализ, сравнение, экспорт … (без изменений) …

    promo = PromoDetector()
    for p in all_products:
        if p.get('image_url'):
            try:
                import tempfile, requests
                r = requests.get(p['image_url'], timeout=10)
                if r.status_code == 200:
                    tf = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    tf.write(r.content); tf.close()
                    p['promotion_analysis'] = promo.predict_promotion(tf.name)
                    os.remove(tf.name)
                else:
                    p['promotion_analysis'] = {"error": "img load failed"}
            except Exception as ex:
                logger.error(ex)
                p['promotion_analysis'] = {"error": str(ex)}
        else:
            p['promotion_analysis'] = {"error": "no image"}

    analysis = {}
    if len(all_products) >= 2:
        analysis = compare_product_data(all_products[-2], all_products[-1])

    csvf, pdff = 'exported.csv', 'exported.pdf'
    try:
        export_to_csv(all_products, csvf)
        export_to_pdf(all_products, pdff)
    except Exception as e:
        logger.error(f"Ошибка экспорта: {e}")

    return jsonify({
        "products":   all_products,
        "analysis":   analysis,
        "csv_file":   csvf,
        "pdf_file":   pdff
    })

@app.route('/download/<kind>', methods=['GET'])
def download(kind):
    if kind == 'csv':
        fn = 'exported.csv'
    elif kind == 'pdf':
        fn = 'exported.pdf'
    else:
        return jsonify({"error": "bad type"}), 400
    path = os.path.join(os.getcwd(), fn)
    if not os.path.exists(path):
        return jsonify({"error": "not found"}), 404
    return send_file(path, as_attachment=True, download_name=fn)

@app.route('/products', methods=['GET'])
def list_products():
    out = []
    for p in get_products():
        out.append({
            "id":        p.id,
            "name":      p.name,
            "article":   p.article,
            "price":     p.price,
            "quantity":  p.quantity,
            "image_url": p.image_url,
            "timestamp": getattr(p, "timestamp", None)
        })
    return jsonify(out)

@app.route('/dashboard', methods=['GET'])
def dashboard_data():
    products = list(get_products())
    summary = {"products_count": len(products)}
    if len(products) >= 2:
        try:
            summary["last_compare"] = compare_product_data(products[-2], products[-1])
        except Exception as e:
            summary["error"] = str(e)
    return jsonify(summary)

@app.route('/reports', methods=['GET'])
def reports_data():
    reports_list = []
    if os.path.exists('exported.csv'):
        reports_list.append({"id": "csv", "title": "Экспорт CSV"})
    if os.path.exists('exported.pdf'):
        reports_list.append({"id": "pdf", "title": "Отчёт PDF"})
    return jsonify(reports_list)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
