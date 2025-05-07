import os
import json
import pytest

def test_health_endpoint(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "ok"}

def test_index_page(client):
    html = client.get("/").get_data(as_text=True)
    assert "<h1>Приложение для анализа маркетплейсов</h1>" in html

@pytest.mark.parametrize("cfg", ["", "../bad.conf", "/etc/passwd", "config.txt"])
def test_start_analysis_invalid_path(client, cfg):
    resp = client.post("/start", data={"config_file": cfg})
    assert resp.status_code == 400
    assert "error" in resp.get_json()

def test_start_analysis_missing_urls(client, monkeypatch):
    # Конфиг без SEARCH.urls
    monkeypatch.setattr("backend.config_parser.read_config",
                        lambda p: {"SEARCH": {}})
    resp = client.post("/start", data={"config_file": "dummy.conf"})
    assert resp.status_code == 400
    assert resp.get_json()["error"].startswith("Не указаны URL")

def test_start_analysis_config_read_error(client, monkeypatch):
    def boom(path): raise RuntimeError("oops")
    monkeypatch.setattr("backend.config_parser.read_config", boom)
    resp = client.post("/start", data={"config_file": "dummy.conf"})
    assert resp.status_code == 400
    assert "Ошибка чтения конфигурации" in resp.get_json()["error"]

def test_start_analysis_successful_run(client, monkeypatch):
    # Подменяем read_config и scraper
    dummy = {
        "MARKETPLACES": {},
        "SEARCH": {"urls": "http://x", "categories": "", "time_range": "7"},
        "EXPORT": {"save_to_db": "False"}
    }
    monkeypatch.setattr("backend.config_parser.read_config", lambda p: dummy)
    monkeypatch.setattr("backend.scraper.scrape_marketplace", lambda url, **kw: [
        {"name":"n","article":"a","price":"1","quantity":"2","image_url":""}
    ])
    # Подменяем промо-детектор, экспорт и БД чтобы не делать реальные операции
    class FakePD:
        def predict_promotion(self, ip): return {"promotion_detected": False}
    monkeypatch.setattr("backend.app.PromoDetector", lambda : FakePD())
    monkeypatch.setattr("backend.exporter.export_to_csv", lambda *args,**kw: None)
    monkeypatch.setattr("backend.exporter.export_to_pdf", lambda *args,**kw: None)
    resp = client.post("/start", data={"config_file": "dummy.conf"})
    assert resp.status_code == 200
    j = resp.get_json()
    assert "products" in j and isinstance(j["products"], list)
    assert j["analysis"] == {}
    assert j["csv_file"] == "exported_products.csv"

@pytest.mark.parametrize("ftype,code", [
    ("csv", 404),
    ("pdf", 404),
])
def test_download_not_exist(client, ftype, code):
    resp = client.get(f"/download/{ftype}")
    assert resp.status_code == code

def test_download_invalid_type(client):
    resp = client.get("/download/xyz")
    assert resp.status_code == 400

def test_download_csv_success(client):
    # создаём файл в tmp_path (фикстура client делает cwd=tmp_path)
    with open("exported_products.csv","w",encoding="utf-8") as f:
        f.write("foo,bar\n1,2")
    resp = client.get("/download/csv")
    assert resp.status_code == 200
    assert "attachment" in resp.headers["Content-Disposition"]
    assert "foo,bar" in resp.get_data(as_text=True)

def test_download_pdf_success(client):
    with open("exported_products.pdf","wb") as f:
        f.write(b"%PDF-1.4")
    resp = client.get("/download/pdf")
    assert resp.status_code == 200
    cd = resp.headers["Content-Disposition"]
    assert "exported_products.pdf" in cd
    assert resp.data.startswith(b"%PDF")

def test_list_products_empty(client, monkeypatch):
    monkeypatch.setattr("backend.app.get_products", lambda : [])
    resp = client.get("/products")
    assert resp.status_code == 200
    assert resp.get_json() == []

def test_list_products_nonempty(client, monkeypatch):
    class P: 
        def __init__(self): 
            self.id=5; self.name="n"; self.article="a"
            self.price="1"; self.quantity="2"; self.image_url="u"
            from datetime import datetime; self.timestamp=datetime(2020,1,1)
    monkeypatch.setattr("backend.app.get_products", lambda : [P()])
    resp = client.get("/products")
    arr = resp.get_json()
    assert arr[0]["id"] == 5 and arr[0]["timestamp"].startswith("2020-01-01")
