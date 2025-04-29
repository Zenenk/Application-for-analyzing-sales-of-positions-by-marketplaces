import unittest
from backend.analysis import compare_product_data

class TestAnalysis(unittest.TestCase):
    def test_compare_product_data(self):
        old = {"price": "100 руб.", "quantity": "20", "image_url": "http://example.com/image1.jpg"}
        new = {"price": "110 руб.", "quantity": "18", "image_url": "http://example.com/image2.jpg"}
        result = compare_product_data(old, new)
        # Проверяем правильность расчёта изменений
        self.assertEqual(result["price_change"], 10)         # 110 - 100 = 10
        self.assertEqual(result["quantity_change"], -2)      # 18 - 20 = -2
        self.assertTrue(result["image_changed"])             # URL изображения изменился

if __name__ == "__main__":
    unittest.main()
