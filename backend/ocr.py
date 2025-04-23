import cv2
import pytesseract
import numpy as np
from loguru import logger

def preprocess_image(image_path):
    image = cv2.imread(image_path)
    if image is None:
        logger.error(f"Не удалось открыть изображение {image_path}")
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    ret, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY_INV)
    return thresh

def extract_text_from_image(image_path):
    processed = preprocess_image(image_path)
    if processed is not None:
        text = pytesseract.image_to_string(processed, lang='rus+eng')
        return text.strip()
    return ""
