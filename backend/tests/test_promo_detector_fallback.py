import os
import pytest
from backend.promo_detector import PromoDetector

def test_predict_promotion_when_ocr_fails(monkeypatch, tmp_path):
    """
    Если ocr_image внутри падает — возвращаем prob=0 и пустой keywords.
    """
    import cv2, numpy as np
    # пустое изображение
    img = np.zeros((10,10,3), dtype=np.uint8)
    path = tmp_path/"blank.jpg"
    cv2.imwrite(str(path), img)
    # заставляем OCR бросать
    monkeypatch.setattr("backend.promo_detector.ocr_image", lambda p: (_ for _ in ()).throw(Exception("boom")))
    det = PromoDetector()
    res = det.predict_promotion(str(path))
    assert res["promotion_probability"] == 0.0
    assert res["promotion_detected"] is False
    assert res["detected_keywords"] == []