def analyze_changes(products):
    # Простой анализ: вычисляем изменения цены, если предыдущее значение есть.
    # Для демонстрации – возвращаем список с изменениями (заглушка).
    analysis_results = []
    for product in products:
        # Если в product присутствует поле old_price – вычисляем разницу
        if 'old_price' in product and product['old_price']:
            change = product['price'] - product['old_price']
            analysis_results.append({
                'name': product['name'],
                'change': change,
                'promotion': product.get('promotion', False)
            })
        else:
            analysis_results.append({
                'name': product['name'],
                'change': 0,
                'promotion': product.get('promotion', False)
            })
    return analysis_results
