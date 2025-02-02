import tensorflow as tf
import cv2
import numpy as np
from app.ocr import ocr_image

class PromoDetector:
    def __init__(self, model_path=None):
        """
        Если model_path указан, загружается обученная модель,
        иначе создаётся демонстрационная (dummy) модель.
        """
        if model_path:
            self.model = tf.keras.models.load_model(model_path)
        else:
            self.model = self.build_dummy_model()
    
    def build_dummy_model(self):
        """
        Создаёт простую CNN-модель для демонстрации.
        На практике требуется обучить модель на размеченных данных.
        """
        from tensorflow.keras.models import Sequential
        from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
        model = Sequential([
            Conv2D(16, (3, 3), activation='relu', input_shape=(224, 224, 3)),
            MaxPooling2D(2, 2),
            Conv2D(32, (3, 3), activation='relu'),
            MaxPooling2D(2, 2),
            Flatten(),
            Dense(64, activation='relu'),
            Dropout(0.5),
            Dense(1, activation='sigmoid')  # 1 выход: вероятность того, что на изображении есть элементы акции
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def preprocess_image(self, image_path):
        """
        Загружает изображение, меняет его размер до 224x224 и нормализует.
        Возвращает изображение в виде numpy-массива с размерностью (1, 224, 224, 3).
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Изображение не найдено по указанному пути")
        image = cv2.resize(image, (224, 224))
        image = image.astype("float32") / 255.0
        image = np.expand_dims(image, axis=0)
        return image

    def predict_promotion(self, image_path):
        """
        Выполняет предобработку изображения, получает предсказание нейросетью,
        затем выполняет OCR для извлечения текста и ищет ключевые слова.
        Возвращает словарь с результатами анализа.
        """
        image = self.preprocess_image(image_path)
        # Предсказание вероятности наличия промо-элементов (демо-модель)
        prob = self.model.predict(image)[0][0]
        promotion_detected = prob > 0.5
        # Извлечение текста с изображения с помощью OCR
        ocr_text = ocr_image(image_path)
        # Извлечение ключевых слов из OCR-текста
        detected_keywords = self.extract_keywords(ocr_text)
        return {
            "promotion_detected": promotion_detected,
            "promotion_probability": float(prob),
            "ocr_text": ocr_text,
            "detected_keywords": detected_keywords
        }

    def extract_keywords(self, text):
        """
        Ищет в тексте ключевые слова и фразы, указывающие на акции.
        Список можно расширять.
        """
        keywords_list = [
            "акция", "скидка", "перечеркнутая", "новая цена", "-20%", "-30%", "-50%",
            "2 по цене 3", "2+1", "бонус", "распродажа", "скид", "акционные"
        ]
        detected = []
        text_lower = text.lower()
        for keyword in keywords_list:
            if keyword in text_lower:
                detected.append(keyword)
        return detected

if __name__ == "__main__":
    detector = PromoDetector()
    try:
        result = detector.predict_promotion("sample_product.jpg")
        print("Результаты анализа изображения:")
        print(result)
    except Exception as e:
        print("Ошибка:", e)
