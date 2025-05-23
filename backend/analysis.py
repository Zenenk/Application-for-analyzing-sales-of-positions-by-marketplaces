# backend/analysis.py

import re
from loguru import logger

def compare_product_data(old_data: dict, new_data: dict) -> dict:
    """
    Сравнивает старые и новые данные о продукте.

    Аргументы:
      - old_data: {'price': str, 'quantity': str, 'image_url': str}
      - new_data: {'price': str, 'quantity': str, 'image_url': str}

    Возвращает:
      {
        'price_change': float | None,
        'quantity_change': int   | None,
        'image_changed':  bool
      }
    """
    result = {}

    # 1) Разбор цены, учитывая десятичный разделитель и пробелы
    try:
        def parse_price(s: str) -> float:
            # Оставляем цифры, точки и запятые
            num = re.sub(r"[^\d.,]", "", s or "")
            # Заменяем запятую на точку и приводим к float
            return float(num.replace(",", "."))
        old_price = parse_price(old_data.get("price", "0"))
        new_price = parse_price(new_data.get("price", "0"))
        result["price_change"] = new_price - old_price
    except Exception as e:
        logger.warning(f"Не удалось вычислить изменение цены: {e}")
        result["price_change"] = None

    # 2) Разбор остатков — целые числа
    try:
        old_qty = int(re.sub(r"[^\d]", "", old_data.get("quantity", "") or "0"))
        new_qty = int(re.sub(r"[^\d]", "", new_data.get("quantity", "") or "0"))
        result["quantity_change"] = new_qty - old_qty
    except Exception as e:
        logger.warning(f"Не удалось вычислить изменение остатка: {e}")
        result["quantity_change"] = None

    # 3) Проверка смены URL-а картинки
    result["image_changed"] = old_data.get("image_url") != new_data.get("image_url")

    return result
