from backend.scraper import fetch_ozon_search

for query in ["хлебцы", "хлебцы гречневые"]:
    print(f"Search for: {query}")
    prods = fetch_ozon_search(query, limit=5)
    print(f"  Returned {len(prods)} items")
    for p in prods:
        print("   -", p.get("name"), p.get("price"), p.get("article"))
