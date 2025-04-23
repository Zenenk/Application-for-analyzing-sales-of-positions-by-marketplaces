import cv2
import numpy as np
from loguru import logger
import pytesseract
import tensorflow as tf
from ocr import extract_text_from_image

class PromoDetector:
    def __init__(self, model_path=None):
        if model_path:
            self.model = tf.keras.models.load_model(model_path)
        else:
            self.model = self.build_dummy_model()

    def build_dummy_model(self):
        from tensorflow.keras import layers, models
        model = models.Sequential([
            layers.Conv2D(16, (3,3), activation='relu', input_shape=(224,224,3)),
            layers.MaxPooling2D(2,2),
            layers.Flatten(),
            layers.Dense(1, activation='sigmoid')
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy')
        return model

    def predict_promotion(self, image_url):
        # Здесь делаем простую проверку: если ссылка пустая, возвращаем False
        if not image_url:
            return False
        # Скачиваем изображение
        import requests, tempfile
        response = requests.get(image_url)
        if response.status_code != 200:
            return False
        temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
        with open(temp_file.name, 'wb') as f:
            f.write(response.content)
        # Для демонстрации воспользуемся OCR
        text = extract_text_from_image(temp_file.name).lower()
        keywords = ['скидка', 'акция', '%', '-']
        result = any(kw in text for kw in keywords)
        return result
