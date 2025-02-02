import unittest
import os
from app.exporter import export_to_csv, export_to_pdf

class TestExporter(unittest.TestCase):
    def setUp(self):
        self.products = [
            {"name": "Тест1", "article": "A1", "price": "100 руб.", "quantity": "10", "image_url": "http://example.com/1.jpg"},
            {"name": "Тест2", "article": "A2", "price": "200 руб.", "quantity": "5", "image_url": "http://example.com/2.jpg"}
        ]
        self.csv_filename = "test_products.csv"
        self.pdf_filename = "test_products.pdf"
    
    def tearDown(self):
        if os.path.exists(self.csv_filename):
            os.remove(self.csv_filename)
        if os.path.exists(self.pdf_filename):
            os.remove(self.pdf_filename)
    
    def test_export_to_csv(self):
        export_to_csv(self.products, self.csv_filename)
        self.assertTrue(os.path.exists(self.csv_filename))
    
    def test_export_to_pdf(self):
        export_to_pdf(self.products, self.pdf_filename)
        self.assertTrue(os.path.exists(self.pdf_filename))

if __name__ == "__main__":
    unittest.main()
