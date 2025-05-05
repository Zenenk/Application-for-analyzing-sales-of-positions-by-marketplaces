import os
import pytest
from backend.schedule import run_scheduled_analysis

def test_run_no_urls(tmp_path, monkeypatch):
    # конфига с пустыми urls
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("backend.config_parser.read_config", lambda p: {"SEARCH": {}})
    # ничего не создаётся
    run_scheduled_analysis("dummy.conf")
    assert not os.path.exists("scheduled_products.csv")
    assert not os.path.exists("scheduled_products.pdf")

def test_run_export(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Настраиваем фиктивный конфиг
    monkeypatch.setattr("backend.config_parser.read_config", lambda p: {
        "SEARCH": {"urls": "u1,u2"}, "EXPORT": {"save_to_db": "False"}
    })
    # Два пустых списка продуктов
    monkeypatch.setattr("backend.scraper.scrape_marketplace", lambda url, **kw: [
        {"name":"n","article":"a","price":"1","quantity":"2","image_url":""}
    ])
    # Подменяем экспорт чтобы просто писать «ok»
    monkeypatch.setattr("backend.schedule.export_to_csv", lambda data, fn: open(fn, "w").write("csv"))
    monkeypatch.setattr("backend.schedule.export_to_pdf", lambda data, fn: open(fn, "wb").write(b"pdf"))
    run_scheduled_analysis("dummy.conf")
    # Проверяем, что файлы появились
    assert os.path.exists("scheduled_products.csv")
    assert os.path.exists("scheduled_products.pdf")
    assert open("scheduled_products.csv").read() == "csv"
    with open("scheduled_products.pdf","rb") as f:
        assert f.read()==b"pdf"
