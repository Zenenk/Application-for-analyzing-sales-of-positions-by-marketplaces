# tools/inspect_wb_cards.py

from playwright.sync_api import sync_playwright
import time
import random

URL = "https://www.wildberries.ru/catalog/0/search.aspx?search=хлебцы"
CARD_COUNT = 10

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False, args=["--no-sandbox"])
    ctx = browser.new_context(locale="ru-RU", timezone_id="Europe/Moscow",
                              user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/136.0 Safari/537.36")
    page = ctx.new_page()
    page.goto(URL, wait_until="domcontentloaded")
    # немного прокрутить, чтобы карточки подгрузились
    for _ in range(3):
        page.mouse.wheel(0, 800)
        time.sleep(random.uniform(0.5, 1.0))
    # найти все потенциальные элементы-карточки
    els = page.query_selector_all("div")  # сначала всё, потом отфильтруем
    cards = []
    for el in els:
        # проверяем, содержит ли этот div ссылку на товар
        a = el.query_selector("a[href*='/catalog/']")
        if a:
            href = a.get_attribute("href")
            html = el.inner_html()
            cards.append((href, html))
        if len(cards) >= CARD_COUNT:
            break

    # вывести паттерны
    for idx, (href, html) in enumerate(cards, 1):
        print(f"\n--- CARD #{idx} ---")
        print("Link:", href)
        # обрезаем HTML до первых 300 символов
        print("HTML snippet:", html[:300].replace("\n"," ").strip(), "…")

    browser.close()
