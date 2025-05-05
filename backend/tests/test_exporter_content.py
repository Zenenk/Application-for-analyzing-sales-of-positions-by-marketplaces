import os
import csv
import pytest
from backend.exporter import export_to_csv, export_to_pdf

@pytest.fixture(autouse=True)
def tmp_cwd(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield

def test_export_to_csv_reads_back_identical():
    """CSV содержит ровно те строки, что мы записали."""
    products = [{"name":"X","article":"A","price":"1","quantity":"2","image_url":"u"}]
    fn = "out.csv"
    export_to_csv(products, fn)
    with open(fn, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    assert rows == products

def test_export_to_pdf_header_and_size():
    """PDF создаётся, начинается с %PDF и имеет ненулевой размер."""
    products = [{"name":"N","article":"A","price":"1","quantity":"2","image_url":""}]
    fn = "out.pdf"
    export_to_pdf(products, fn)
    data = open(fn, "rb").read()
    assert data.startswith(b"%PDF")
    assert len(data) > 100