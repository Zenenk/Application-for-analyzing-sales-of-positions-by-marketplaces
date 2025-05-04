import unittest
import cv2
import numpy as np
import os
from ocr import ocr_image

class TestOCR(unittest.TestCase):
    def setUp(self):
        # Генерируем тестовое изображение с текстом "Тест"
        self.image_path = "test_image.jpg"
        img = np.ones((100, 300, 3), dtype=np.uint8) * 255  # белый фон
        cv2.putText(img, "Тест", (5, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
        cv2.imwrite(self.image_path, img)

    def tearDown(self):
        # Удаляем тестовое изображение
        if os.path.exists(self.image_path):
            os.remove(self.image_path)

    def test_ocr_image(self):
        text = ocr_image(self.image_path)
        # Проверяем, что распознанный текст содержит исходное слово "Тест"
        self.assertIn("Тест", text)

if __name__ == "__main__":
    unittest.main()
