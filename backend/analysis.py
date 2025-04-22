def compare_product_data(old_data, new_data):
    """
    Сравнивает старые и новые данные о продукте.
    
    Словари содержат ключи: price, quantity, image_url.
    Возвращает словарь с изменениями:
      - price_change: разница в цене (числовое значение)
      - quantity_change: разница в остатках (целое число)
      - image_changed: True, если ссылка на изображение изменилась
    """
    result = {}
    try:
        old_price = float(''.join(filter(str.isdigit, old_data.get("price", "0"))))
        new_price = float(''.join(filter(str.isdigit, new_data.get("price", "0"))))
        result["price_change"] = new_price - old_price
    except Exception:
        result["price_change"] = None

    try:
        old_quantity = int(''.join(filter(str.isdigit, old_data.get("quantity", "0"))))
        new_quantity = int(''.join(filter(str.isdigit, new_data.get("quantity", "0"))))
        result["quantity_change"] = new_quantity - old_quantity
    except Exception:
        result["quantity_change"] = None

    result["image_changed"] = old_data.get("image_url") != new_data.get("image_url")
    return result

if __name__ == "__main__":
    old = {"price": "100 руб.", "quantity": "20", "image_url": "http://example.com/image1.jpg"}
    new = {"price": "110 руб.", "quantity": "18", "image_url": "http://example.com/image2.jpg"}
    print(compare_product_data(old, new))
