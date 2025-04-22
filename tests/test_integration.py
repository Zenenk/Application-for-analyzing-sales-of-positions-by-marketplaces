import unittest
import json
from backend.app import app

class IntegrationTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
    
    def test_index_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
    
    def test_start_analysis_invalid_config(self):
        response = self.client.post('/start', data={"config_file": "non_existent.conf"})
        self.assertEqual(response.status_code, 400)
    
    def test_start_analysis_with_dummy_product(self):
        #mock для подмены функций чтения конфига и скрейпера
        from unittest.mock import patch
        dummy_product = {
            "name": "Тестовый продукт",
            "article": "TP001",
            "price": "100 руб.",
            "quantity": "10",
            # Для теста используется placeholder-изображение, доступное по HTTP
            "image_url": "https://via.placeholder.com/150"
        }
        with patch("app.scraper.scrape_marketplace", return_value=[dummy_product]), \
             patch("app.config_parser.read_config", return_value={
                "MARKETPLACES": {"marketplaces": "Test"},
                "SEARCH": {"urls": "http://dummy-url", "categories": "Тест", "time_range": "7"},
                "EXPORT": {"format": "CSV", "save_to_db": "False"}
             }):
            response = self.client.post('/start', data={"config_file": "dummy.conf"})
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn("products", data)
            # Проверяем, что в возвращённом товаре присутствует анализ промо-изображения
            if data["products"]:
                product = data["products"][0]
                self.assertIn("promotion_analysis", product)
                # Если изображение было успешно обработано, ожидаем ключи в анализе
                if "error" not in product["promotion_analysis"]:
                    self.assertIn("promotion_detected", product["promotion_analysis"])
                    self.assertIn("promotion_probability", product["promotion_analysis"])
                    self.assertIn("ocr_text", product["promotion_analysis"])
                    self.assertIn("detected_keywords", product["promotion_analysis"])

if __name__ == "__main__":
    unittest.main()
