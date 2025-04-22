import unittest
import os
import cv2
import numpy as np
from backend.promo_detector import PromoDetector

class DummyModel:
    def predict(self, image):
        # Возвращает фиксированное значение (0.8), что означает наличие акции
        return np.array([[0.8]])

class TestPromoDetector(unittest.TestCase):
    def setUp(self):
        self.detector = PromoDetector()
        #dummy для тестирования
        self.detector.model = DummyModel()
        # Создаём тестовое изображение с текстом, содержащим промо-выражение
        self.test_image_path = "test_promo.jpg"
        img = np.ones((300, 300, 3), dtype=np.uint8) * 255
        cv2.putText(img, "скидка -20%", (50, 150), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        cv2.imwrite(self.test_image_path, img)
    
    def tearDown(self):
        if os.path.exists(self.test_image_path):
            os.remove(self.test_image_path)

    def test_preprocess_image(self):
        processed = self.detector.preprocess_image(self.test_image_path)
        self.assertEqual(processed.shape, (1, 224, 224, 3))
    
    def test_extract_keywords(self):
        sample_text = "Большая скидка -20%"
        keywords = self.detector.extract_keywords(sample_text)
        self.assertIn("скидка", keywords)
        self.assertIn("-20%", keywords)
    
    def test_predict_promotion(self):
        result = self.detector.predict_promotion(self.test_image_path)
        self.assertTrue(result["promotion_detected"])
        self.assertGreater(result["promotion_probability"], 0.5)
        self.assertIsInstance(result["ocr_text"], str)
        self.assertIn("скидка", result["detected_keywords"])

if __name__ == "__main__":
    unittest.main()
