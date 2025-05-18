# backend/utils/marketplace_urls.py

import urllib.parse

def build_search_url(marketplace: str, query: str) -> str:
    """
    Возвращает корректный URL для страницы категории на маркетплейсе.
    :param marketplace: 'ozon' или 'wildberries'
    :param query: название категории (например, 'хлебцы')
    """
    q = urllib.parse.quote(query)
    if marketplace.lower() == "ozon":
        # пример: https://www.ozon.ru/category/produkty-pitaniya-9200/?…&text=хлебцы
        return (
            "https://www.ozon.ru/category/produkty-pitaniya-9200/"
            "?category_was_predicted=true"
            "&deny_category_prediction=true"
            "&from_global=true"
            f"&text={q}"
        )
    elif marketplace.lower() == "wildberries":
        # пример: https://www.wildberries.ru/catalog/0/search.aspx?search=хлебцы
        return f"https://www.wildberries.ru/catalog/0/search.aspx?search={q}"
    else:
        raise ValueError(f"Неподдерживаемый marketplace: {marketplace}")

def build_product_url(marketplace: str, article: str) -> str:
    """
    Возвращает корректный URL для страницы товара по его артикулу.
    :param marketplace: 'ozon' или 'wildberries'
    :param article: числовой артикул (например, '1605229466')
    """
    a = urllib.parse.quote(article)
    if marketplace.lower() == "ozon":
        # универсальный URL без челночного слага
        # пример: https://www.ozon.ru/context/detail/id/1707473661
        return f"https://www.ozon.ru/context/detail/id/{a}"
    elif marketplace.lower() == "wildberries":
        # пример: https://www.wildberries.ru/catalog/238356171/detail.aspx
        return f"https://www.wildberries.ru/catalog/{a}/detail.aspx"
    else:
        raise ValueError(f"Неподдерживаемый marketplace: {marketplace}")
