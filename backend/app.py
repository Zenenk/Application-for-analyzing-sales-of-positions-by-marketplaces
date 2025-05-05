from flask import Flask, request, jsonify, send_file
import os
# Импортируем модули конфигурации и скрейпера как отдельные модули
import backend.config_parser as config_parser
import backend.scraper as scraper
from backend.database import init_db, add_product, get_products
from backend.exporter import export_to_csv, export_to_pdf
from backend.analysis import compare_product_data
from backend.promo_detector import PromoDetector
from flask_cors import CORS
from loguru import logger

# Создаем Flask-приложение
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
CORS(app, resources={r"/*": {"origins": os.getenv("ALLOWED_ORIGIN", "http://localhost:3000")}})

# Инициализируем базу данных
init_db()
@app.route('/health', methods=['GET'])
def health():
    """Health-check endpoint."""
    return jsonify({"status": "ok"}), 200

@app.route('/')
def index():
    # Простая HTML-страница с формой для запуска анализа
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
    # Получаем путь до конфигурационного файла из формы
    config_path = request.form.get("config_file", "config/config.conf")
    if not config_path or config_path.startswith("/") or ".." in config_path or not config_path.endswith(".conf"):
        return jsonify({"error": "Недопустимый путь конфигурационного файла"}), 400
    try:
        settings = config_parser.read_config(config_path)
    except Exception as e:
        # Если файл не найден или произошла ошибка парсинга, возвращаем HTTP 400
        return jsonify({"error": f"Ошибка чтения конфигурации: {e}"}), 400

    search_settings = settings.get("SEARCH", {})
    urls = search_settings.get("urls", "")
    if not urls:
        return jsonify({"error": "Не указаны URL в конфигурационном файле"}), 400

    url_list = [url.strip() for url in urls.split(",")]
    category_filter = [cat.strip() for cat in search_settings.get("categories", "").split(",") if cat.strip()]
    article_filter = []  # Пока фильтр по артикулам из конфигурации не используется, оставляем пустым

    all_products = []
    # Обходим все указанные URL и собираем данные о продуктах
    for url in url_list:
        try:
            products = scraper.scrape_marketplace(url, category_filter=category_filter, article_filter=article_filter)
        except Exception as e:
            logger.error(f"Ошибка при сборе данных с {url}: {e}")
            continue
        # Сохраняем в базу данных, если в конфигурации указано сохранение
        if settings.get("EXPORT", {}).get("save_to_db", "False").lower() == "true":
            for product in products:
                try:
                    add_product(product)
                except Exception as e:
                    logger.error(f"Ошибка сохранения продукта в базу: {e}")
        all_products.extend(products)

    # Анализ промо-изображений каждого товара (первое изображение)
    promo_detector = PromoDetector()  # инициализируем детектор акций (TensorFlow модель или dummy-модель)
    for product in all_products:
        if product.get("image_url"):
            try:
                # Пытаемся загрузить изображение
                import requests, tempfile
                response = requests.get(product["image_url"], timeout=10)
                if response.status_code == 200:
                    # Сохраняем во временный файл для анализа
                    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                    tmp_file.write(response.content)
                    tmp_file_path = tmp_file.name
                    tmp_file.close()
                    # Анализируем изображение на наличие промо-элементов
                    promotion_result = promo_detector.predict_promotion(tmp_file_path)
                    product["promotion_analysis"] = promotion_result
                    os.remove(tmp_file_path)
                else:
                    product["promotion_analysis"] = {"error": "Не удалось загрузить изображение"}
            except Exception as e:
                logger.error(f"Ошибка анализа изображения: {e}")
                product["promotion_analysis"] = {"error": str(e)}
        else:
            product["promotion_analysis"] = {"error": "Изображение отсутствует"}

    # Если есть хотя бы два товара, сравниваем последние два собранных товара
    analysis_result = {}
    if len(all_products) >= 2:
        analysis_result = compare_product_data(all_products[-2], all_products[-1])
    else:
        analysis_result = {}

    # Экспортируем результаты в файлы CSV и PDF
    csv_filename = "exported_products.csv"
    pdf_filename = "exported_products.pdf"
    try:
        export_to_csv(all_products, csv_filename)
        export_to_pdf(all_products, pdf_filename)
    except Exception as e:
        logger.error(f"Ошибка экспорта файлов: {e}")
        # Если экспорт не удался, продолжаем без выброса исключения

    # Возвращаем результат в формате JSON
    return jsonify({
        "products": all_products,
        "analysis": analysis_result,
        "csv_file": csv_filename,
        "pdf_file": pdf_filename
    })

@app.route('/download/<file_type>', methods=['GET'])
def download_file(file_type):
     # Эндпоинт для скачивания файлов экспорта. Ищем только в текущей директории
    if file_type == "csv":
        filename = "exported_products.csv"
    elif file_type == "pdf":
        filename = "exported_products.pdf"
    else:
        return jsonify({"error": "Неверный тип файла"}), 400

    path = os.path.join(os.getcwd(), filename)
    if not os.path.exists(path):
        return jsonify({"error": "Файл не найден"}), 404

    # Отправляем файл, имя вложения соответствует filename
    return send_file(path, as_attachment=True, download_name=filename)

@app.route('/products', methods=['GET'])
def list_products():
    # Эндпоинт для получения списка всех продуктов из базы (из таблицы products)
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
            "timestamp": p.timestamp.isoformat() if hasattr(p, "timestamp") else None
        })
    return jsonify(products_list)

if __name__ == "__main__":
    # Запуск Flask-приложения
    app.run(host="0.0.0.0", port=5000, debug=True)
