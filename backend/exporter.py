"""Exporter module for saving analysis results to files (CSV or PDF)."""
import csv
from fpdf import FPDF
from backend import database, analysis

def export_all(fmt: str = "csv") -> str:
    """Экспортирует все товары и их историю в файл указанного формата.
    Возвращает путь к созданному файлу, либо None при ошибке.
    """
    products = database.get_all_products()
    if fmt == "csv":
        filename = "export_results.csv"
        try:
            with open(filename, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Заголовок CSV
                writer.writerow(["Product ID", "Marketplace", "Title", "Current Price", "Current Stock", 
                                 "In Promo", "Price Change (%)", "Min Price", "Max Price", "Stock Change"])
                for product in products:
                    history = [h.to_dict() for h in database.get_history(product.id)]
                    trends = analysis.compute_trends(history)
                    writer.writerow([
                        product.id,
                        product.marketplace,
                        product.title,
                        product.price,
                        product.stock if product.stock is not None else "",
                        "Yes" if product.in_promo else "No",
                        trends.get("price_change_pct", ""),
                        trends.get("min_price", ""),
                        trends.get("max_price", ""),
                        trends.get("stock_change", "")
                    ])
            return filename
        except Exception as e:
            print(f"CSV export failed: {e}")
            return None
    elif fmt == "pdf":
        filename = "export_results.pdf"
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 14)
            pdf.cell(0, 10, "Marketplace Analysis Export", ln=1, align='C')
            pdf.set_font("Arial", size=10)
            for product in products:
                history = [h.to_dict() for h in database.get_history(product.id)]
                trends = analysis.compute_trends(history)
                # Добавляем информацию о каждом продукте
                pdf.cell(0, 10, f"[{product.marketplace}] {product.title}", ln=1)
                pdf.cell(0, 8, f"Current price: {product.price} | Stock: {product.stock} | In promo: {product.in_promo}", ln=1)
                if trends:
                    pdf.cell(0, 8, f"Price change: {trends.get('price_change_pct', 'N/A')}% (min {trends.get('min_price')} - max {trends.get('max_price')})", ln=1)
                    if "stock_change" in trends:
                        pdf.cell(0, 8, f"Stock change: {trends['stock_change']} (from {trends['initial_stock']} to {trends['latest_stock']})", ln=1)
                pdf.ln(5)  # пустая строка между продуктами
            pdf.output(filename)
            return filename
        except Exception as e:
            print(f"PDF export failed: {e}")
            return None
    else:
        # Неподдерживаемый формат
        return None
