import unittest
import os
from backend.config_parser import read_config

class TestConfigParser(unittest.TestCase):
    def setUp(self):
        # Создаем временный конфигурационный файл для теста
        self.test_config_file = "test_config.conf"
        config_content = (
            "[MARKETPLACES]\n"
            "marketplaces = Ozon, Wildberries\n\n"
            "[SEARCH]\n"
            "categories = хлебцы, хлебцы гречневые\n"
            "urls = https://www.ozon.ru/category/produkty, https://www.wildberries.ru/catalog/produkty\n"
            "time_range = 7\n\n"
            "[EXPORT]\n"
            "format = CSV\n"
            "save_to_db = True\n"
        )
        with open(self.test_config_file, "w", encoding="utf-8") as f:
            f.write(config_content)

    def tearDown(self):
        # Удаляем временный файл после тестов
        if os.path.exists(self.test_config_file):
            os.remove(self.test_config_file)

    def test_read_config(self):
        settings = read_config(self.test_config_file)
        # Проверяем, что разделы и параметры считаны правильно
        self.assertIn("MARKETPLACES", settings)
        self.assertIn("SEARCH", settings)
        self.assertEqual(settings["MARKETPLACES"]["marketplaces"], "Ozon, Wildberries")
        self.assertEqual(settings["SEARCH"]["time_range"], "7")
        self.assertEqual(settings["EXPORT"]["format"], "CSV")

if __name__ == "__main__":
    unittest.main()
