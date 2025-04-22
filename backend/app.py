from flask import Flask, request, jsonify, send_file
from backend.config_parser import read_config
from backend.scraper import scrape_marketplace
from backend.database import init_db, add_product, get_products
from backend.exporter import export_to_csv, export_to_pdf
from backend.analysis import compare_product_data
import os

app = Flask(__name__)

init_db()

@app.route('/')
def index():
    return """
    <h1>Приложение для анализа маркетплейсов</h1>
    <form action="/start" method="post">
      <label for="config_file">Путь к конфигурационному файлу:</label>
      <input type="text" id="config_file" name="config_file" value="config/config.conf"><br><br>
      <input type="submit" value="Начать анализ">
    </form>
    """

@app.route('/start', methods=['POST'])
def start_analysis():
    config_file = request.form.get("config_file", "config/config.conf")
    try:
        settings = read_config(config_file)
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    
    search_settings = settings.get("SEARCH", {})
    urls = search_settings.get("urls", "")
    if not urls:
        return jsonify({"error": "Не указаны URL в конфигурационном файле"}), 400
    url_list = [url.strip() for url in urls.split(",")]
    category_filter = [cat.strip() for cat in search_settings.get("categories", "").split(",")]
    article_filter = []
    
    all_products = []
    for url in url_list:
        products = scrape_marketplace(url, category_filter=category_filter, article_filter=article_filter)
        if settings.get("EXPORT", {}).get("save_to_db", "False").lower() == "true":
            for product in products:
                add_product(product)
        all_products.extend(products)
    
    # Анализ первого изображения каждого товара с помощью promo_detector
    from backend.promo_detector import PromoDetector
    import requests, tempfile
    promo_detector = PromoDetector()
    for product in all_products:
        if product.get("image_url"):
            try:
                response = requests.get(product["image_url"])
                if response.status_code == 200:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                        tmp_file.write(response.content)
                        tmp_file_path = tmp_file.name
                    promotion_result = promo_detector.predict_promotion(tmp_file_path)
                    product["promotion_analysis"] = promotion_result
                    os.remove(tmp_file_path)
                else:
                    product["promotion_analysis"] = {"error": "Не удалось загрузить изображение"}
            except Exception as e:
                product["promotion_analysis"] = {"error": str(e)}
        else:
            product["promotion_analysis"] = {"error": "Изображение отсутствует"}
    
    # Сравнение двух последних товаров
    analysis_result = {}
    if len(all_products) >= 2:
        analysis_result = compare_product_data(all_products[-2], all_products[-1])
    
    # Экспорт результатов
    csv_filename = "exported_products.csv"
    pdf_filename = "exported_products.pdf"
    export_to_csv(all_products, csv_filename)
    export_to_pdf(all_products, pdf_filename)
    
    return jsonify({
        "products": all_products,
        "analysis": analysis_result,
        "csv_file": csv_filename,
        "pdf_file": pdf_filename
    })

@app.route('/download/<file_type>', methods=['GET'])
def download_file(file_type):
    if file_type == "csv":
        filename = "exported_products.csv"
    elif file_type == "pdf":
        filename = "exported_products.pdf"
    else:
        return jsonify({"error": "Неверный тип файла"}), 400
    
    if not os.path.exists(filename):
        return jsonify({"error": "Файл не найден"}), 404
    return send_file(filename, as_attachment=True)

@app.route('/products', methods=['GET'])
def list_products():
    products = get_products()
    products_list = []
    for p in products:
        products_list.append({
            "id": p.id,
            "name": p.name,
            "article": p.article,
            "price": p.price,
            "quantity": p.quantity,
            "image_url": p.image_url,
            "timestamp": p.timestamp.isoformat()
        })
    return jsonify(products_list)

if __name__ == "__main__":
    app.run(debug=True)
