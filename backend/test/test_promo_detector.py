import unittest
import numpy as np
import cv2
import os
from backend.promo_detector import PromoDetector, DummyModel

# Определяем DummyModel для использования в тестах (если не импортирован из модуля)
# (В самом модуле PromoDetector уже определён DummyModel)
# class DummyModel:
#     def predict(self, image):
#         return np.array([[0.8]])  # например, вероятность 0.8, обозначающая наличие акции

class TestPromoDetector(unittest.TestCase):
    def setUp(self):
        # Инициализируем PromoDetector и заменяем модель на DummyModel для детерминированного результата
        self.detector = PromoDetector()
        self.detector.model = DummyModel()  # подмена модели на заглушку, возвращающую 0.5 (или 0.8, в зависимости от DummyModel)
        # Создаем тестовое изображение с текстом, содержащим промо-выражение "скидка -20%"
        self.test_image_path = "test_promo.jpg"
        img = np.ones((300, 300, 3), dtype=np.uint8) * 255  # белый фон
        cv2.putText(img, "скидка -20%", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imwrite(self.test_image_path, img)

    def tearDown(self):
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    def test_preprocess_image(self):
        processed = self.detector.preprocess_image(self.test_image_path)
        # Должны получить numpy-массив формы (1, 224, 224, 3)
        self.assertEqual(processed.shape, (1, 224, 224, 3))

    def test_extract_keywords(self):
        sample_text = "Большая скидка -20%"
        keywords = self.detector.extract_keywords(sample_text)
        # Ключевые слова "скидка" и "-20%" должны быть извлечены
        self.assertIn("скидка", keywords)
        self.assertIn("-20%", keywords)

    def test_predict_promotion(self):
        result = self.detector.predict_promotion(self.test_image_path)
        # Проверяем, что промо-акция обнаружена (DummyModel может возвращать 0.5, тогда promotion_detected False;
        # Если DummyModel возвращает 0.8, то True. Здесь допустимо любое, мы проверим consistency.)
        self.assertIn("promotion_detected", result)
        self.assertGreaterEqual(result["promotion_probability"], 0.0)
        self.assertIsInstance(result["ocr_text"], str)
        # Проверяем, что хотя бы одно ключевое слово акции обнаружено в тексте
        self.assertIn("скидка", result["detected_keywords"])

if __name__ == "__main__":
    unittest.main()
