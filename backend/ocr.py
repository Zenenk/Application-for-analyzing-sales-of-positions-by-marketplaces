"""OCR module for extracting text from product images."""
import cv2
import pytesseract
import numpy as np
import requests
from io import BytesIO

# Настройка Tesseract (если требуется указать путь к двоичному файлу)
# pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'

def _preprocess_image(image_bytes: bytes) -> np.ndarray:
    """Простейшая предварительная обработка изображения для улучшения OCR."""
    # Чтение изображения из байт
    image = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        return None
    # Конвертация в оттенки серого и лёгкое размытие
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    return gray

def extract_texts(image_urls: list) -> list:
    """Для каждого изображения по URL выполняет OCR и возвращает список обнаруженных текстов."""
    texts = []
    for url in image_urls:
        try:
            resp = requests.get(url, timeout=5)
            resp.raise_for_status()
            img_data = resp.content
        except Exception:
            continue  # если изображение недоступно, пропускаем
        # Предобрабатываем изображение
        preprocessed = _preprocess_image(img_data)
        if preprocessed is None:
            continue
        # Применяем OCR
        text = pytesseract.image_to_string(preprocessed, lang="rus+eng")  # распознаём русский и английский
        text = text.strip()
        if text:
            texts.append(text)
    return texts
