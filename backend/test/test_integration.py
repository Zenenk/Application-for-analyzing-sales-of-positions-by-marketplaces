import unittest
import json
from backend.app import app
from unittest.mock import patch

class IntegrationTest(unittest.TestCase):
    def setUp(self):
        # Создаем тестовый клиент Flask
        self.client = app.test_client()

    def test_index_page(self):
        response = self.client.get('/')
        # Ожидаем, что главная страница возвращается успешно (HTTP 200)
        self.assertEqual(response.status_code, 200)

    def test_start_analysis_invalid_config(self):
        # Отправляем запрос с несуществующим конфиг-файлом
        response = self.client.post('/start', data={"config_file": "non_existent.conf"})
        # Ожидаем код ошибки 400
        self.assertEqual(response.status_code, 400)

    def test_start_analysis_with_dummy_product(self):
        # Подменяем функции чтения конфигурации и скрейпера на фиктивные для изоляции теста
        dummy_product = {
            "name": "Тестовый продукт",
            "article": "TP001",
            "price": "100 руб.",
            "quantity": "10",
            # Используем реальное изображение-заглушку (placeholder) для предсказуемого OCR
            "image_url": "https://via.placeholder.com/150"
        }
        with patch("backend.config_parser.read_config", return_value={
            "MARKETPLACES": {"marketplaces": "Test"},
            "SEARCH": {"urls": "http://dummy-url", "categories": "Тест", "time_range": "7"},
            "EXPORT": {"format": "CSV", "save_to_db": "False"}
        }), patch("backend.scraper.scrape_marketplace", return_value=[dummy_product]):
            response = self.client.post('/start', data={"config_file": "dummy.conf"})
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        # Проверяем, что результат содержит список продуктов
        self.assertIn("products", data)
        if data["products"]:
            product = data["products"][0]
            # Должен присутствовать ключ с результатом анализа промо-изображения
            self.assertIn("promotion_analysis", product)
            # Если анализ выполнен без ошибки, проверяем наличие ожидаемых полей
            if "error" not in product["promotion_analysis"]:
                self.assertIn("promotion_detected", product["promotion_analysis"])
                self.assertIn("promotion_probability", product["promotion_analysis"])
                self.assertIn("ocr_text", product["promotion_analysis"])
                self.assertIn("detected_keywords", product["promotion_analysis"])

if __name__ == "__main__":
    unittest.main()
