"""
Модуль для обнаружения промо-акций на изображении товара.
Использует простую модель (TensorFlow/Keras) и OCR для анализа.
"""
import numpy as np
import cv2
from backend.ocr import ocr_image

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
except ImportError:
    # Если TensorFlow не установлен, выбросить исключение при попытке использования
    tf = None

class PromoDetector:
    def __init__(self, model_path=None):
        """
        Инициализирует детектор промо.
        Настраивает модель классификации текста (TF-IDF + LogisticRegression) для выявления промо-меток.
        """
        # Инициализируем классификатор текста для промо-меток
        self.vectorizer = TfidfVectorizer()
        self.classifier = LogisticRegression(max_iter=1000)
        # Обучаем модель классификации на примерах промо и без промо
        promo_texts = ["скидка", "акция", "распродажа", "sale", "discount", "специальное предложение"]
        nonpromo_texts = ["товар", "новинка", "описание", "в наличии", "на складе", "обычная цена"]
        X_train = promo_texts + nonpromo_texts
        y_train = [1]*len(promo_texts) + [0]*len(nonpromo_texts)
        X_vectors = self.vectorizer.fit_transform(X_train)
        self.classifier.fit(X_vectors, y_train)

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
            "акция", "скидка", "новая цена",
            "-5%", "-10%", "-15%", "-20%", "-25%", "-30%", "-35%", "-40%", "-45%", "-50%", 
            "-55%", "-60%", "-65%", "-70%", "-75%", "-80%", "-85%", "-90%", "-95%", "1+1" "2+1", 
            "3+1", "4+1", "5+1", "4+2", "5+2","бонус", "распродажа", "праздник цен", "персональная привилегия",
            "привлекательные условия", "эксклюзивная акция", "межсезонная распродажа",
            "распродажа перед праздниками", "финальная распродажа",
            "sale", "Black Friday", "mid-season sale", "holiday sale", "outlet"
            "final sale", "clearance", "special offer", "discount", "further reductions",
            "5%% off", "10%% off", "15%% off", "20%% off", "25%% off", "30%% off",
            "35%% off", "40%% off", "45%% off", "50%% off", "55%% off", "60%% off", 
            "65%% off", "70%% off", "75%% off", "80%% off", "85%% off", "90%% off", "95%% off",
            "buy one, get one free" , "deal of the day", "closeout"
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
        # Распознаем текст на изображении (OCR)
        ocr_text = ""
        try:
            ocr_text = ocr_image(image_path)
        except Exception as e:
            ocr_text = ""
        # Определяем вероятность промо-акции по распознанному тексту
        if ocr_text:
            X_test = self.vectorizer.transform([ocr_text])
            prob = float(self.classifier.predict_proba(X_test)[0][1])
        else:
            prob = 0.0
        promotion_detected = (prob > 0.5)
        # Выделяем ключевые слова из текста
        detected_keywords = self.extract_keywords(ocr_text)
        return {
            "promotion_detected": promotion_detected,
            "promotion_probability": float(prob),
            "ocr_text": ocr_text,
            "detected_keywords": detected_keywords
        }

# Тестирование PromoDetector в автономном режиме
if __name__ == "__main__":
    detector = PromoDetector()
    try:
        result = detector.predict_promotion("sample_product.jpg")
        print("Результаты анализа изображения:", result)
    except Exception as e:
        print("Ошибка анализа изображения:", e)
