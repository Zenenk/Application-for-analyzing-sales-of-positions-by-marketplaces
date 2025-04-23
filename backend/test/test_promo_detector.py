from promo_detector import PromoDetector

def test_predict_promotion():
    detector = PromoDetector()
    # Пример тестового URL изображения; если изображение не достучалось, функция вернет False
    result = detector.predict_promotion("https://via.placeholder.com/150")
    assert isinstance(result, bool)
