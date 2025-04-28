"""
Модуль для обнаружения промо-акций на изображении товара.
Использует простую модель (TensorFlow/Keras) и OCR для анализа.
"""
import numpy as np
import cv2
from backend.ocr import ocr_image

try:
    import tensorflow as tf
except ImportError:
    # Если TensorFlow не установлен, можно выбросить исключение при попытке использования
    tf = None

class PromoDetector:
    def __init__(self, model_path=None):
        """
        Инициализирует детектор промо. Если указан путь к сохранённой модели (model_path), загрузит модель,
        иначе создаст простую CNN-модель (необученную) для демо.
        """
        if model_path and tf:
            # Загрузка обученной модели из файла
            self.model = tf.keras.models.load_model(model_path)
        else:
            # Создаем демо-модель (необученную) или заглушку, если TensorFlow недоступен
            if tf:
                self.model = self.build_dummy_model()
            else:
                # Если TensorFlow не доступен, используем простую заглушку
                self.model = DummyModel()

    def build_dummy_model(self):
        """
        Создаёт простую CNN Sequential модель в Keras для определения наличия промо-элементов.
        (Демонстрационная модель с 1 выходом: вероятность наличия промо.)
        """
        model = tf.keras.models.Sequential([
            tf.keras.layers.Conv2D(16, (3, 3), activation='relu', input_shape=(224, 224, 3)),
            tf.keras.layers.MaxPooling2D(2, 2),
            tf.keras.layers.Conv2D(32, (3, 3), activation='relu'),
            tf.keras.layers.MaxPooling2D(2, 2),
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(64, activation='relu'),
            tf.keras.layers.Dropout(0.5),
            tf.keras.layers.Dense(1, activation='sigmoid')  # 1 выходной нейрон: вероятность акции
        ])
        model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        return model

    def preprocess_image(self, image_path):
        """
        Загружает изображение с диска, меняет размер до 224x224 и нормализует пиксели.
        Возвращает подготовленный тензор изображения формы (1, 224, 224, 3).
        """
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("Изображение не найдено по указанному пути")
        # Приводим к нужному размеру
        image = cv2.resize(image, (224, 224))
        # Нормализуем в диапазон [0,1]
        image = image.astype("float32") / 255.0
        # Добавляем размерность батча
        image = np.expand_dims(image, axis=0)
        return image

    def extract_keywords(self, text):
        """
        Ищет в распознанном тексте ключевые слова и паттерны, указывающие на промо-акции.
        Возвращает список найденных ключевых слов.
        """
        keywords_list = [
            "акция", "скидка", "перечеркнутая", "новая цена",
            "-20%", "-30%", "-50%", "2+1", "бонус", "распродажа"
        ]
        detected = []
        text_lower = text.lower()
        for keyword in keywords_list:
            if keyword in text_lower:
                detected.append(keyword)
        return detected

    def predict_promotion(self, image_path):
        """
        Анализирует изображение на наличие промо-элементов.
        Шаги:
          1. Предобработка изображения и получение вероятности наличия промо с помощью модели.
          2. OCR для извлечения текста с изображения.
          3. Выделение ключевых слов из текста.
        Возвращает словарь с результатами:
          - promotion_detected: bool, обнаружена ли акция.
          - promotion_probability: вероятность акции (float).
          - ocr_text: распознанный текст.
          - detected_keywords: список ключевых слов, связанных с акциями.
        """
        # Предобработка изображения
        image = self.preprocess_image(image_path)
        # Если TensorFlow недоступен, используем DummyModel
        if tf is None and isinstance(self.model, DummyModel):
            prob = self.model.predict(image)[0][0]
        else:
            prob = float(self.model.predict(image)[0][0])
        promotion_detected = (prob > 0.5)
        # Распознаем текст на изображении
        ocr_text = ""
        try:
            ocr_text = ocr_image(image_path)
        except Exception as e:
            ocr_text = ""
        # Выделяем ключевые слова из OCR-текста
        detected_keywords = self.extract_keywords(ocr_text)
        return {
            "promotion_detected": promotion_detected,
            "promotion_probability": float(prob),
            "ocr_text": ocr_text,
            "detected_keywords": detected_keywords
        }

# Дополнительный класс-заглушка для модели (используется при отсутствии TensorFlow)
class DummyModel:
    def predict(self, image):
        # Возвращает фиксированную вероятность 0.5 (50%) в виде нужного формата массива
        return np.array([[0.5]])

# Тестирование PromoDetector в автономном режиме
if __name__ == "__main__":
    detector = PromoDetector()
    try:
        result = detector.predict_promotion("sample_product.jpg")
        print("Результаты анализа изображения:", result)
    except Exception as e:
        print("Ошибка анализа изображения:", e)
