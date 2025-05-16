# backend/screenshot_importer.py
"""
Скрипт для распознавания текста на скриншоте страницы категории или товара
и сохранения извлечённых параметров в базу данных.
Использует EasyOCR для извлечения текста.
"""
import re
import sys
import easyocr
from backend.database import add_product

# Инициализация OCR-ридера (русский и английский)
_reader = easyocr.Reader(['ru', 'en'], gpu=False)


def parse_screenshot(image_path: str, marketplace: str) -> dict:
    """
    Распознаёт текст на изображении и извлекает ключевые параметры:
      - article (артикул товара)
      - price_new (новая цена)
      - price_old (старая цена)
      - discount (размер скидки)
      - promo_labels (список промо-лейблов как текст)

    :param image_path: путь к файлу-скриншоту
    :param marketplace: код маркетплейса, например, 'ozon' или 'wildberries'
    :return: словарь с извлечёнными данными
    """
    # Запуск OCR
    texts = _reader.readtext(image_path, detail=0)
    # Объединяем все фрагменты в одну строку
    full_text = ' '.join(texts)

    # Ищем артикул: 'Артикул: 12345678'
    m = re.search(r'[Аа]ртикул[:\s]*([0-9]+)', full_text)
    article = m.group(1) if m else ''

    # Ищем все вхождения цен (число + ₽)
    price_matches = re.findall(r'(\d+[ \d]*?)\s*₽', full_text)
    price_new = ''
    price_old = ''
    if price_matches:
        # Считаем, что первая цена — текущая (окрашенная), вторая — перечёркнутая
        price_new = price_matches[0]
        if len(price_matches) > 1:
            price_old = price_matches[1]

    # Ищем скидки формата '-52%'
    d = re.search(r'-?\d+%+', full_text)
    discount = d.group(0) if d else ''

    # Ищем ключевые промо-лейблы (встречающиеся слова)
    promo_labels = []
    for label in ['распродажа', 'хорошая цена', 'sale', 'discount']:
        if label.lower() in full_text.lower():
            promo_labels.append(label)

    # Формируем результирующий словарь
    result = {
        'article':       article,
        'price_new':     price_new,
        'price_old':     price_old,
        'discount':      discount,
        'promo_labels':  promo_labels,
        'marketplace':   marketplace
    }
    return result


def import_from_screenshot(image_path: str, marketplace: str) -> None:
    """
    Распознаёт и сохраняет данные в БД через add_product.
    """
    data = parse_screenshot(image_path, marketplace)
    # Готовим структуру для add_product
    product_data = {
        'name':             '',  # имя можно оставить пустым или добавить OCR-распознавание заголовка
        'article':          data['article'],
        'price':            data['price_new'],
        'quantity':         '',
        'image_url':        '',
        'promotion_detected': bool(data['discount'] or data['promo_labels']),
        'detected_keywords': ';'.join(data['promo_labels']),
        'price_old':        data['price_old'],
        'price_new':        data['price_new'],
        'discount':         data['discount'],
        'promo_labels':     ';'.join(data['promo_labels']),
        'parsed_at':        None,
    }
    add_product(product_data)
    print(f"Данные импортированы в БД: {product_data}")


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Использование: python screenshot_importer.py <путь_к_изображению> <marketplace>")
        sys.exit(1)
    img_path = sys.argv[1]
    mp = sys.argv[2]
    import_from_screenshot(img_path, mp)
    sys.exit(0)
