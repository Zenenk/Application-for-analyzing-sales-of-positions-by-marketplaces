"""
Модуль OCR: распознавание текста на изображениях с помощью OpenCV и Tesseract.
"""
import cv2
import pytesseract

def ocr_image(image_path):
    """
    Выполняет распознавание текста на изображении.

    Аргументы:
      - image_path: путь к изображению (файл).

    Возвращает:
      - Распознанный текст (строка). Если текст не распознан, возвращает пустую строку.
    """
    # Читаем изображение
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Изображение не найдено по указанному пути")
    # Конвертируем в оттенки серого
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Бинаризация изображения для улучшения качества OCR
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    # Распознаём текст (русский + английский языки)
    text = pytesseract.image_to_string(thresh, lang="rus+eng")
    return text.strip()

# Пример запуска OCR на изображении
if __name__ == "__main__":
    sample_text = ocr_image("sample_product.jpg")
    print("Распознанный текст:", sample_text)
