"""
Модуль OCR: распознавание текста на изображениях с помощью предварительно обученной модели (EasyOCR).
"""
import os
import easyocr

# Создаем OCR-модель один раз при импортировании модуля (используются заранее обученные веса EasyOCR)
_reader = easyocr.Reader(['ru', 'en'], gpu=False)

def ocr_image(image_path: str) -> str:
    """
    Выполняет распознавание текста на изображении с помощью OCR-модели.
    
    Args:
      image_path: путь к файлу изображения.
    
    Returns:
      Распознанный текст (строка).
    """
    # Проверяем, что файл изображения существует
    if not os.path.isfile(image_path):
        raise ValueError(f"Image not found at path: {image_path}")
    try:
        # Получаем список распознанных фрагментов текста
        text_segments = _reader.readtext(image_path, detail=0)
    except Exception:
        # Если при работе OCR произошла ошибка, возвращаем пустую строку
        return ""
    # Объединяем все сегменты текста в одну строку
    text = " ".join(text_segments)
    return text.strip()
