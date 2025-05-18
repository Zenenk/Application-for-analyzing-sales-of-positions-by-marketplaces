# backend/screenshot_importer.py

import os
import re
import logging
from PIL import Image
import pytesseract
from backend.scraper import scrape_marketplace
from backend.database import add_product

logger = logging.getLogger(__name__)

def parse_screenshot(image_path: str, marketplace: str) -> dict:
    """
    Распознаёт на скриншоте:
      - article       — артикул, если это product-page
      - category_name — название категории, если это category-page
      - price_new, price_old, discount, promo_labels
    """
    img = Image.open(image_path)
    full_text = pytesseract.image_to_string(img, lang="rus+eng")

    # 1) Ищем артикул (только на product-page)
    m = re.search(r'[Аа]ртикул[:\s]*([0-9]+)', full_text)
    article = m.group(1) if m else ""

    # 2) Ищем название категории (например, после слова «Каталог» или в хлебных крошках)
    cat = ""
    m2 = re.search(r'(?:Каталог|\/catalog)[\s–:]*([А-Яа-яA-Za-z0-9\- ]{3,50})', full_text)
    if m2:
        cat = m2.group(1).strip()

    # 3) Цены и скидки
    prices = re.findall(r'(\d+[ \d]*?)\s*₽', full_text)
    price_new, price_old = (prices + ["", ""])[0], (prices + ["", ""])[1]
    d = re.search(r'-?\d+%', full_text)
    discount = d.group(0) if d else ""
    labels = []
    for token in ("распродажа","sale","скидка","coupon"):
        if token.lower() in full_text.lower():
            labels.append(token)

    return {
        "article":       article,
        "category_name": cat,
        "price_new":     price_new,
        "price_old":     price_old,
        "discount":      discount,
        "promo_labels":  labels
    }


def import_from_screenshot(image_path: str, marketplace: str, limit: int = 10) -> dict:
    """
    Пытается распарсить скриншот:
      - если увидели article → fetch по товару и сохранить
      - иначе, если category_name → fetch по категории, первые N items
      - иначе возвращает {'status': 'no_article', 'message': ...}
    Возвращает словарь с результатом для фронта.
    """
    os.makedirs("uploads", exist_ok=True)
    data = parse_screenshot(image_path, marketplace)
    art = data["article"]
    cat = data["category_name"]

    # 1) Если артикул найден — скрапим одну страницу товара
    if art:
        logger.info(f"Screenshoter detected ARTICLE={art}")
        prods = scrape_marketplace(
            url=art,
            category_filter=None,
            article_filter=[art],
            limit=1,
            marketplace=marketplace
        )
        if not prods:
            return {"status":"error","message":f"По артикулу {art} ничего не найдено"}

        # сохраняем именно этот товар
        for p in prods:
            add_product({
                "name":             p.get("name",""),
                "article":          p.get("article",""),
                "price":            str(p.get("price","")),
                "quantity":         str(p.get("quantity","")),
                "image_url":        p.get("image_url",""),
                "promotion_detected": bool(data["discount"] or data["promo_labels"]),
                "detected_keywords":  ";".join(data["promo_labels"]),
                "price_old":         data["price_old"],
                "price_new":         data["price_new"],
                "discount":          data["discount"],
                "promo_labels":      ";".join(data["promo_labels"]),
                "parsed_at":         None,
                "marketplace":       marketplace,
                "category":          ""
            })
        return {"status":"ok","imported":1, "type":"product", "article":art}

    # 2) Если артикул НЕ нашли, но есть category_name — скрапим эту категорию
    if cat:
        logger.info(f"Screenshoter detected CATEGORY={cat}")
        # строим URL как в UI (заменим пробелы на %20)
        from urllib.parse import quote
        q = quote(cat)
        url_map = {
            "ozon":        f"https://www.ozon.ru/category/produkty-pitaniya-9200/?text={q}",
            "wildberries": f"https://www.wildberries.ru/catalog/0/search.aspx?search={q}"
        }
        url = url_map.get(marketplace.lower())
        if not url:
            return {"status":"error","message":"Неподдерживаемый marketplace"}

        prods = scrape_marketplace(
            url=url,
            category_filter=[cat],
            article_filter=None,
            limit=limit,
            marketplace=marketplace
        )
        if not prods:
            return {"status":"error","message":f"В категории {cat} ничего не найдено"}

        # сохраняем все найденные позиции
        for idx, p in enumerate(prods, start=1):
            add_product({
                "name":             p.get("name",""),
                "article":          p.get("article",""),
                "price":            str(p.get("price","")),
                "quantity":         str(p.get("quantity","")),
                "image_url":        p.get("image_url",""),
                "promotion_detected": p.get("promotion_analysis",{}).get("promotion_detected",False),
                "detected_keywords":  ";".join(p.get("promotion_analysis",{}).get("detected_keywords",[])),
                "price_old":         p.get("price_old",""),
                "price_new":         p.get("price_new",""),
                "discount":          p.get("discount",""),
                "promo_labels":      ";".join(p.get("promo_labels",[])),
                "parsed_at":         p.get("parsed_at"),
                "marketplace":       marketplace,
                "category":          cat
            })
        return {"status":"ok","imported":len(prods), "type":"category", "category":cat}

    # 3) Иначе — пункт ни то ни другое
    return {"status":"no_article","message":"На скриншоте не найден артикул и не распознана категория"}
