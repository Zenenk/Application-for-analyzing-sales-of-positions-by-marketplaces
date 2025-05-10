"""
Модуль для обнаружения промо-акций на изображении товара.
Использует OCR + ключевые слова и паттерны.
"""
import re
from backend.ocr import ocr_image

# Ключевые слова и символы, указывающие на промо
PROMO_KEYWORDS = [
    "скид", "акция", "распродажа", "sale", "discount", "%"
]

def detect_promo_text(text: str) -> bool:
    """
    Проверяет распознанный текст на наличие промо-маркировок.
    """
    t = text.lower()
    for kw in PROMO_KEYWORDS:
        if kw in t:
            return True
    # Ищем цифру + знак %
    if re.search(r"\d{1,3}\s?%", t):
        return True
    return False

def extract_promo_text(text: str) -> str:
    """
    Извлекает из текста первое упоминание скидки в формате 'XX%'.
    """
    t = text.lower()
    m = re.search(r"\d{1,3}\s?%", t)
    if m:
        return m.group(0).strip()
    # Если нет %, ищем ключевое слово
    for kw in PROMO_KEYWORDS:
        if kw in t:
            return kw
    return ""

class PromoDetector:
    """
    Детектор промо-акций: OCR + проверка ключевых слов.
    """
    def __init__(self):
        # Никакого обучения — работаем по правилам
        pass

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
            kw = extract_promo_text(text)
            if kw:
                result["detected_keywords"].append(kw)
        return result
