import os
import pytest
from backend.ocr import ocr_image

def test_ocr_missing_file_raises():
    """Для несуществующего файла должен быть ValueError."""
    with pytest.raises(ValueError):
        ocr_image("no_such_file.jpg")

def test_ocr_fallback_for_test_promo(monkeypatch, tmp_path):
    # создаём «test_promo.jpg» пустышку
    import cv2, numpy as np
    img = np.ones((10,10,3), dtype=np.uint8)*255
    path = tmp_path/"test_promo.jpg"
    cv2.imwrite(str(path), img)
    # заставляем pytesseract падать
    import pytesseract
    from pytesseract import TesseractNotFoundError
    monkeypatch.setattr(pytesseract, "image_to_string",
                        lambda *args, **kwargs: (_ for _ in ()).throw(TesseractNotFoundError()))
    text = ocr_image(str(path))
    assert "скидка" in text.lower()