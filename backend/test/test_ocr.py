from ocr import extract_text_from_image
import os

def test_extract_text_from_image():
    # Используйте подготовленное тестовое изображение с текстом "АКЦИЯ 50%"
    test_image = os.path.join(os.path.dirname(__file__), 'sample_promo.jpg')
    text = extract_text_from_image(test_image)
    assert "акция" in text.lower() or "50" in text
