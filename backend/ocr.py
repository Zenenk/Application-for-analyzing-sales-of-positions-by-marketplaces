"""
Модуль OCR: распознавание текста на изображениях с помощью OpenCV и Tesseract.
"""
import os
import cv2
import pytesseract
from pytesseract import TesseractNotFoundError

def ocr_image(image_path: str) -> str:
    """
    Выполняет распознавание текста на изображении.

    Args:
      image_path: путь к файлу изображения.

    Returns:
      Распознанный текст (строка).
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Image not found at path: {image_path}")

    # Конвертируем в оттенки серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Адаптивная бинаризация + морфологическое закрытие для шумоподавления
    thresh = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11, 2
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    try:
        text = pytesseract.image_to_string(
            thresh,
            lang="rus+eng",
            config="--psm 6"
        )
    except TesseractNotFoundError:
        # Если Tesseract не установлен, возвращаем пустую строку
        return ""

    return text.strip()
