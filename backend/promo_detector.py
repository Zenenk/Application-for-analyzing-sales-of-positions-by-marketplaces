"""
Модуль для обнаружения промо-акций на изображении товара.
Использует OCR (распознавание текста) + поиск ключевых слов и шаблонов.
"""
import re
import os
import cv2
import numpy as np
from ocr import ocr_image

# Ключевые слова и символы, указывающие на промо
PROMO_KEYWORDS = [
    "скидка", "акция", "распродажа", "sale", "discount", "%"
]

def detect_promo_text(text: str) -> bool:
    """
    Проверяет распознанный текст на наличие промо-маркировок.
    """
    t = text.lower()
    for kw in PROMO_KEYWORDS:
        if kw in t:
            return True
    # Ищем последовательность цифр (1-3 знака) перед знаком %
    if re.search(r"\d{1,3}\s?%", t):
        return True
    return False

class PromoDetector:
    """
    Детектор промо-акций: использует OCR + проверку ключевых слов.
    """
    def __init__(self):
        pass

    def preprocess_image(self, image_path: str):
        """
        Предобрабатывает изображение для входа модели (например, масштабирует до 224x224).
        
        Args:
          image_path: путь к файлу изображения.
        
        Returns:
          Нормализованный массив изображения формы (1, 224, 224, 3).
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Image not found at path: {image_path}")
        # Масштабируем изображение до размера 224x224
        image_resized = cv2.resize(image, (224, 224))
        # Добавляем размер батча (axis=0)
        image_batch = np.expand_dims(image_resized, axis=0)
        return image_batch

    def extract_keywords(self, text: str) -> list:
        """
        Извлекает все ключевые слова и выражения, относящиеся к промо-акциям.
        
        Например, из строки "Большая скидка -20%" вернет ["-20%", "скидка"].
        """
        t = text.lower()
        keywords_found = []
        # Ищем все шаблоны вида -?XX%
        percent_matches = re.findall(r"-?\d{1,3}\s?%", t)
        for match in percent_matches:
            token = match.strip()
            if token and token not in keywords_found:
                keywords_found.append(token)
        # Ищем все вхождения ключевых слов из списка
        for kw in PROMO_KEYWORDS:
            if kw == "%":
                continue  # пропускаем отдельный символ %, мы уже обработали проценты выше
            if kw in t:
                # Получаем полный фрагмент (слово) текста, содержащий ключевое слово
                match = re.search(rf"\b\w*{re.escape(kw)}\w*\b", t)
                if match:
                    token = match.group(0)
                else:
                    token = kw
                if token and token not in keywords_found:
                    keywords_found.append(token)
        return keywords_found

    def predict_promotion(self, image_path: str) -> dict:
        """
        Анализирует изображение:
          - Распознаёт текст (OCR)
          - Проверяет ключевые слова/паттерны
          - Возвращает dict с результатами
        """
        try:
            text = ocr_image(image_path)
        except Exception:
            text = ""
        promo_flag = detect_promo_text(text)
        result = {
            "promotion_detected": promo_flag,
            "promotion_probability": 1.0 if promo_flag else 0.0,
            "ocr_text": text,
            "detected_keywords": []
        }
        if promo_flag:
            result["detected_keywords"] = self.extract_keywords(text)
        return result
