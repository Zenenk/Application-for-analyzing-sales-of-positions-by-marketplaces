
---

#### backend/app.py
```python
import os
from flask import Flask, jsonify, request, make_response, send_file
from flask_sqlalchemy import SQLAlchemy
from loguru import logger
from flasgger import Swagger
from database import db, init_db
from config_parser import read_config
from scraper import scrape_marketplace
from analysis import analyze_changes
from exporter import export_to_csv, export_to_pdf
from schedule import start_scheduler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///data/monitoring.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'super_secret_key')
app.config['SWAGGER'] = {
    "title": "Marketplace Monitoring API",
    "uiversion": 3
}

db.init_app(app)
swagger = Swagger(app)

with app.app_context():
    init_db()

# Простой API-токен для защиты (проверяем в каждом запросе)
def check_api_token():
    token = request.headers.get('Authorization')
    if not token or token.split(" ")[-1] != os.getenv('API_TOKEN'):
        return False
    return True

@app.before_request
def before_request():
    # Для публичных эндпоинтов можно исключить проверку, здесь проверяем все
    if not check_api_token():
        return jsonify({'error': 'Unauthorized'}), 401

@app.route('/api/items', methods=['GET'])
def get_items():
    # Получение списка товаров (реализовано в database.py)
    from database import get_all_items
    items = get_all_items()
    return jsonify(items)

@app.route('/api/items', methods=['POST'])
def add_item():
    # Добавление нового товара для мониторинга
    data = request.get_json()
    from database import add_item_to_db
    item = add_item_to_db(data)
    return jsonify(item), 201

@app.route('/api/export/csv', methods=['GET'])
def download_csv():
    csv_path = export_to_csv()
    return send_file(csv_path, as_attachment=True, download_name="report.csv", mimetype='text/csv')

@app.route('/api/export/pdf', methods=['GET'])
def download_pdf():
    pdf_path = export_to_pdf()
    return send_file(pdf_path, as_attachment=True, download_name="report.pdf", mimetype='application/pdf')

@app.route('/api/config', methods=['GET'])
def get_config():
    config = read_config('config/monitoring.yaml')
    return jsonify(config)

@app.route('/api/config', methods=['PUT'])
def update_config():
    new_config = request.get_json()
    # Запись в файл (упрощённая реализация)
    import yaml
    with open('config/monitoring.yaml', 'w', encoding='utf-8') as f:
        yaml.safe_dump(new_config, f, allow_unicode=True)
    return jsonify(new_config)

@app.route('/api/analysis', methods=['POST'])
def run_analysis():
    # Выполнить сбор и анализ данных
    config = read_config('config/monitoring.yaml')
    logger.info("Начало сбора данных")
    results = scrape_marketplace(config)
    analysis = analyze_changes(results)
    # Можно сохранить результаты анализа в базу
    return jsonify({'results': results, 'analysis': analysis})

if __name__ == '__main__':
    # Запуск планировщика для автоматического сбора данных
    start_scheduler(app)
    app.run(host='0.0.0.0', port=5000)
