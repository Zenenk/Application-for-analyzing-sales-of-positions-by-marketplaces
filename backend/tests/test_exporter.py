import pytest
import os
from backend.exporter import export_to_csv, export_to_pdf

def read_lines(p):
    return p.read_text(encoding="utf-8").splitlines()

def test_export_csv_empty(tmp_path):
    out = tmp_path / "empty.csv"
    export_to_csv([], str(out))
    lines = read_lines(out)
    assert lines == ["name,article,price,quantity,image_url"]

def test_export_csv_multiple(tmp_path):
    data = [
        {"name":"n1","article":"a1","price":"p1","quantity":"q1","image_url":"u1"},
        {"name":"n2","article":"a2","price":"p2","quantity":"q2","image_url":"u2"},
    ]
    out = tmp_path / "multi.csv"
    export_to_csv(data, str(out))
    lines = read_lines(out)
    assert lines[0].startswith("name,article")
    assert lines[1] == "n1,a1,p1,q1,u1"
    assert lines[2] == "n2,a2,p2,q2,u2"

@pytest.mark.parametrize("count, min_size", [
    (1, 100),       # для одного товара PDF >100 байт
    (100, 3000),    # для 100 товаров PDF >3000 байт
])
def test_export_pdf(tmp_path, count, min_size):
    data = [{"name":str(i),"article":"a","price":"p","quantity":"q","image_url":""} for i in range(count)]
    out = tmp_path / "out.pdf"
    export_to_pdf(data, str(out))
    size = out.stat().st_size
    # Проверяем, что PDF создан и не слишком маленький
    assert size > min_size, f"PDF слишком маленький: {size} <= {min_size}"
    # должен начинаться с "%PDF"
    with open(out, "rb") as f:
        assert f.read(4) == b"%PDF"
