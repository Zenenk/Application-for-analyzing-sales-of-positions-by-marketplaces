import cv2
import pytesseract

def ocr_image(image_path):
    """
    Распознавание текста на изображении.
    
    Аргументы:
      - image_path: путь к изображению.
      
    Возвращает распознанный текст.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError("Изображение не найдено по указанному пути")
    
    # Предобработка: конвертация в оттенки серого и бинаризация
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    
    text = pytesseract.image_to_string(thresh, lang="rus+eng")
    return text.strip()

if __name__ == "__main__":
    text = ocr_image("sample_product.jpg")
    print("Распознанный текст:", text)
