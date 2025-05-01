
"""
Модуль анализа данных о продуктах
"""

def compare_product_data(old_data, new_data):
    """
    Сравнивает старые и новые данные о продукте.

    Аргументы:
      - old_data: словарь с предыдущими данными товара (ключи: price, quantity, image_url).
      - new_data: словарь с новыми данными товара.

    Возвращает словарь с изменениями:
      - price_change: разница в цене (число) или None, если вычислить не удалось.
      - quantity_change: разница в остатке на складе (целое) или None.
      - image_changed: True, если ссылка на изображение изменилась, иначе False.
    """
    result = {}
    try:
        # Извлекаем числовое значение из строки цены (игнорируя валюту и пробелы)
        old_price = float(''.join(filter(str.isdigit, old_data.get("price", "") or "0")))
        new_price = float(''.join(filter(str.isdigit, new_data.get("price", "") or "0")))
        result["price_change"] = new_price - old_price
    except Exception as e:
        logger.warning(f"Не удалось вычислить изменение цены: {e}")
        result["price_change"] = None

    try:
        # Извлекаем числовое значение из остатка
        old_quantity = int(''.join(filter(str.isdigit, old_data.get("quantity", "") or "0")))
        new_quantity = int(''.join(filter(str.isdigit, new_data.get("quantity", "") or "0")))
        result["quantity_change"] = new_quantity - old_quantity
    except Exception as e:
        logger.warning(f"Не удалось вычислить изменение остатка: {e}")
        result["quantity_change"] = None

    # Проверяем изменение изображения (сравниваем URL)
    result["image_changed"] = (old_data.get("image_url") != new_data.get("image_url"))
    return result

if __name__ == "__main__":
    old = {"price": "100 руб.", "quantity": "20", "image_url": "http://example.com/image1.jpg"}
    new = {"price": "110 руб.", "quantity": "18", "image_url": "http://example.com/image2.jpg"}
    print(compare_product_data(old, new))
