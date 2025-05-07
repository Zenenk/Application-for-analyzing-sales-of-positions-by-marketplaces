# backend/tests/test_app.py

import os
import pytest
import tempfile
import json
from flask import Flask
from backend.app import app
import backend.config_parser as config_parser
import backend.scraper as scraper
import backend.exporter as exporter

@pytest.fixture(autouse=True)
def working_dir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield

@pytest.fixture
def client():
    """
    Возвращает тестовый клиент Flask с включённым режимом TESTING.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    """GET /health должен возвращать статус ok и код 200."""
    resp = client.get('/health')
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == {"status": "ok"}

def test_index_page(client):
    """GET / должен вернуть HTML с формой запуска анализа."""
    resp = client.get('/')
    assert resp.status_code == 200
    body = resp.get_data(as_text=True)
    assert '<form action="/start" method="post">' in body
    assert 'name="config_file"' in body
    assert '<input type="submit" value="Начать анализ">' in body

@pytest.mark.parametrize("bad_path", [
    "",          # пустая строка
    "../bad.conf",
    "/etc/passwd",
    "config.txt" # неправильное расширение
])
def test_start_analysis_invalid_path(client, bad_path):
    """POST /start с недопустимым путём конфигурации даёт 400."""
    resp = client.post('/start', data={'config_file': bad_path})
    assert resp.status_code == 400
    assert resp.is_json
    assert "error" in resp.get_json()

def test_start_analysis_missing_urls(client, monkeypatch):
    """POST /start, если в конфиге нет SEARCH.urls — 400 и соответствующая ошибка."""
    fake_settings = {"SEARCH": {}, "EXPORT": {}}
    monkeypatch.setattr(config_parser, 'read_config', lambda path: fake_settings)
    resp = client.post('/start', data={'config_file': 'dummy.conf'})
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Не указаны URL в конфигурационном файле"}

def test_start_analysis_config_read_error(client, monkeypatch):
    """POST /start, если read_config бросает исключение — 400 и текст ошибки."""
    def boom(path):
        raise Exception("parse error")
    monkeypatch.setattr(config_parser, 'read_config', boom)
    resp = client.post('/start', data={'config_file': 'dummy.conf'})
    assert resp.status_code == 400
    json_body = resp.get_json()
    assert "Ошибка чтения конфигурации" in json_body.get("error", "")

def test_start_analysis_successful_run(client, monkeypatch):
    """
    POST /start с валидным конфигом и заглушкой скрейпера:
    - отрабатывает без ошибок;
    - возвращает JSON с ключами products, analysis, csv_file, pdf_file.
    """
    # Заглушки для конфига и скрейпера
    dummy_prod = {
        "name": "Товар",
        "article": "A1",
        "price": "100",
        "quantity": "1",
        "image_url": ""
    }
    fake_settings = {
        "SEARCH": {"urls": "url1,url2", "categories": "", "time_range": "7"},
        "EXPORT": {"save_to_db": "False", "format": "CSV"}
    }
    monkeypatch.setattr(config_parser, 'read_config', lambda path: fake_settings)
    monkeypatch.setattr(scraper, 'scrape_marketplace', lambda url, category_filter, article_filter: [dummy_prod])
    # Заглушки экспорта, чтобы не создавать реальные файлы
    monkeypatch.setattr(exporter, 'export_to_csv', lambda products, fn: None)
    monkeypatch.setattr(exporter, 'export_to_pdf', lambda products, fn: None)

    resp = client.post('/start', data={'config_file': 'dummy.conf'})
    assert resp.status_code == 200
    data = resp.get_json()
    # Проверяем структуру
    assert isinstance(data, dict)
    assert "products" in data and isinstance(data["products"], list)
    assert "analysis" in data and isinstance(data["analysis"], dict)
    assert data["csv_file"] == "exported_products.csv"
    assert data["pdf_file"] == "exported_products.pdf"

@pytest.mark.parametrize("ftype,status", [
    ("csv", 404),  # файла ещё нет
    ("pdf", 404),
])
def test_download_not_exist(client, ftype, status):
    """GET /download/{csv,pdf} при отсутствии файла — 404."""
    # Убедимся, что файла нет
    for fn in ("exported_products.csv","exported_products.pdf"):
        if os.path.exists(fn):
            os.remove(fn)
    resp = client.get(f'/download/{ftype}')
    assert resp.status_code == status
    assert resp.is_json
    assert resp.get_json() == {"error": "Файл не найден"}

def test_download_invalid_type(client):
    """GET /download/invalid — 400 и JSON {error: 'Неверный тип файла'}."""
    resp = client.get('/download/badtype')
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Неверный тип файла"}

def test_download_csv_success(client):
    """GET /download/csv после создания файла — отдаёт attachment CSV."""
    # Создадим файл
    with open("exported_products.csv", "w", encoding="utf-8") as f:
        f.write("col1,col2\n1,2")
    resp = client.get('/download/csv')
    assert resp.status_code == 200
    # Заголовок отдачи
    cd = resp.headers.get("Content-Disposition","")
    assert "attachment" in cd and "exported_products.csv" in cd
    # Контент
    assert b"col1,col2" in resp.data

def test_download_pdf_success(client):
    """GET /download/pdf после создания файла — отдаёт attachment PDF."""
    # Создадим pdf-файл
    with open("exported_products.pdf", "wb") as f:
        f.write(b"%PDF")
    resp = client.get('/download/pdf')
    assert resp.status_code == 200
    cd = resp.headers.get("Content-Disposition","")
    assert "attachment" in cd and "exported_products.pdf" in cd
    assert resp.data.startswith(b"%PDF")

def test_list_products_empty(client):
    """GET /products на свежем БД — возвращает пустой список."""
    resp = client.get('/products')
    assert resp.status_code == 200
    assert resp.is_json
    assert resp.get_json() == []


def client(tmp_path, monkeypatch):
    # Чтобы и download, и любые файловые операции работали в tmp_path
    monkeypatch.chdir(tmp_path)
    with app.test_client() as client:
        yield client

def test_index_page(client):
    """GET / возвращает HTML с формой."""
    resp = client.get('/')
    assert resp.status_code == 200
    html = resp.get_data(as_text=True)
    assert '<h1>Приложение для анализа маркетплейсов</h1>' in html

@pytest.mark.parametrize("cfg,err", [
    ("/etc/passwd", "Недопустимый путь"),
    ("../evil.conf", "Недопустимый путь"),
    ("noext.txt", "Недопустимый путь"),
])
def test_start_invalid_path(client, cfg, err):
    resp = client.post('/start', data={"config_file": cfg})
    assert resp.status_code == 400
    assert err in resp.get_json()["error"]

def test_start_read_config_error(client, monkeypatch):
    """Если read_config бросает, возвращаем 400 с текстом ошибки."""
    def bad_read(p): raise ValueError("boom!")
    monkeypatch.setattr("backend.app.config_parser.read_config", bad_read)
    resp = client.post('/start', data={"config_file": "ok.conf"})
    assert resp.status_code == 400
    assert "Ошибка чтения конфигурации" in resp.get_json()["error"]

def test_start_no_urls(client, monkeypatch):
    """Если в секции SEARCH нет urls, 400."""
    monkeypatch.setattr("backend.app.config_parser.read_config", lambda p: {"SEARCH": {}})
    resp = client.post('/start', data={"config_file": "ok.conf"})
    assert resp.status_code == 400
    assert "Не указаны URL" in resp.get_json()["error"]

def test_download_invalid_type(client):
    """GET /download/xyz → 400."""
    resp = client.get("/download/xyz")
    assert resp.status_code == 400
    assert resp.get_json() == {"error": "Неверный тип файла"}

def test_download_not_exists(client):
    """GET /download/csv/pdf при отсутствии файлов → 404."""
    for t in ("csv","pdf"):
        resp = client.get(f"/download/{t}")
        assert resp.status_code == 404
        assert resp.get_json() == {"error": "Файл не найден"}

def test_download_csv_success(client, tmp_path):
    """GET /download/csv после создания файла отдаёт attachment."""
    fname = tmp_path / "exported_products.csv"
    fname.write_text("col1,col2\n1,2", encoding="utf-8")
    resp = client.get("/download/csv")
    assert resp.status_code == 200
    cd = resp.headers["Content-Disposition"]
    assert "attachment" in cd and "exported_products.csv" in cd
    assert b"col1,col2" in resp.data

def test_list_products(client, monkeypatch):
    """GET /products возвращает JSON-список, преобразуя timestamp."""
    class P: 
        id=42; name="N"; article="A"; price="P"; quantity="Q"; image_url="URL"
        def __init__(self):
            self.timestamp = __import__("datetime").datetime(2021,1,1,12,0,0)
        def __repr__(self): return "<P>"
    monkeypatch.setattr("backend.app.get_products", lambda: [P()])
    resp = client.get("/products")
    assert resp.status_code == 200
    arr = resp.get_json()
    assert arr == [{
        "id": 42, "name": "N", "article": "A", "price": "P", 
        "quantity": "Q", "image_url": "URL",
        "timestamp": "2021-01-01T12:00:00"
    }]