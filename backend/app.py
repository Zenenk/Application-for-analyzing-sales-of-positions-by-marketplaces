from flask import Flask, request, jsonify, send_file
import os
from loguru import logger
from flask_cors import CORS

import backend.config_parser as config_parser
from backend.database import init_db, add_product, get_products
from backend.exporter import export_to_csv, export_to_pdf
from backend.analysis import compare_product_data
from backend.promo_detector import PromoDetector
import backend.scraper as scraper  # теперь с Playwright

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
# Разрешаем запросы от фронтенда (если ALLOWED_ORIGIN не задан, разрешаем для всех)
origins = os.getenv('ALLOWED_ORIGIN', '*')
CORS(app, resources={r"/*": {"origins": origins}})

# init DB
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
      <input type="text" name="save_html" placeholder="dump.html (optional)" />
      <button type="submit">Начать анализ</button>
    </form>
    """

@app.route('/start', methods=['POST'])
def start_analysis():
    # 1) читаем конфиг
    file = request.files.get('config_file')
    if not file:
        return jsonify({"error": "Нет файла конфигурации"}), 400
    path = os.path.join('config', file.filename)
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

    # promo-анализ
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

    # сравнение последних двух для динамики
    analysis = {}
    if len(all_products) >= 2:
        analysis = compare_product_data(all_products[-2], all_products[-1])

    # экспорт
    csvf, pdff = 'exported.csv', 'exported.pdf'
    try:
        export_to_csv(all_products, csvf)
        export_to_pdf(all_products, pdff)
    except Exception as e:
        logger.error(f"Ошибка экспорта: {e}")

    return jsonify({
        "products": all_products,
        "analysis": analysis,
        "csv_file": csvf,
        "pdf_file": pdff
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
            "id": p.id,
            "name": p.name,
            "article": p.article,
            "price": p.price,
            "quantity": p.quantity,
            "image_url": p.image_url,
            "timestamp": getattr(p, "timestamp", None)
        })
    return jsonify(out)

@app.route('/dashboard', methods=['GET'])
def dashboard_data():
    # Сводные данные для дашборда: количество товаров и сравнение последних двух
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
    # Список отчётов (CSV, PDF), которые можно скачать
    reports_list = []
    if os.path.exists('exported.csv'):
        reports_list.append({"id": "csv", "title": "Экспорт CSV"})
    if os.path.exists('exported.pdf'):
        reports_list.append({"id": "pdf", "title": "Отчёт PDF"})
    return jsonify(reports_list)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
