import unittest
import os
from app.config_parser import read_config

class TestConfigParser(unittest.TestCase):
    def setUp(self):
        # Создаем временный конфигурационный файл
        self.test_config_file = "test_config.conf"
        with open(self.test_config_file, "w", encoding="utf-8") as f:
            f.write(
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

    def tearDown(self):
        os.remove(self.test_config_file)

    def test_read_config(self):
        settings = read_config(self.test_config_file)
        self.assertIn("MARKETPLACES", settings)
        self.assertIn("SEARCH", settings)
        self.assertEqual(settings["MARKETPLACES"]["marketplaces"], "Ozon, Wildberries")
        self.assertEqual(settings["SEARCH"]["time_range"], "7")
        self.assertEqual(settings["EXPORT"]["format"], "CSV")

if __name__ == "__main__":
    unittest.main()
