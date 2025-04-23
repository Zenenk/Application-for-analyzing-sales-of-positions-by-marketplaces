from exporter import export_to_csv, export_to_pdf
import os

def test_export_to_csv():
    csv_path = export_to_csv()
    assert os.path.exists(csv_path)
    os.remove(csv_path)

def test_export_to_pdf():
    pdf_path = export_to_pdf()
    assert os.path.exists(pdf_path)
    os.remove(pdf_path)
