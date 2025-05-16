// comparator for multi-key sort
export function sortByHierarchy(a, b) {
    // 1) timestamp (новые сначала)
    const ta = new Date(a.timestamp), tb = new Date(b.timestamp);
    if (ta > tb) return -1;
    if (ta < tb) return 1;
  
    // 2) article (строковый/числовой)
    if (a.article !== b.article) {
      // если артикулы — числа в строках, можно парсить:
      const na = isNaN(+a.article) ? a.article : +a.article;
      const nb = isNaN(+b.article) ? b.article : +b.article;
      return na < nb ? -1 : na > nb ? 1 : 0;
    }
  
    // 3) discount (проценты) — убывание
    const da = parseFloat(a.discount) || 0;
    const db = parseFloat(b.discount) || 0;
    if (da !== db) return db - da;
  
    // 4) price — возрастание
    const pa = parseFloat(a.price) || 0;
    const pb = parseFloat(b.price) || 0;
    if (pa !== pb) return pa - pb;
  
    // 5) quantity — возрастание
    const qa = parseInt(a.quantity, 10) || 0;
    const qb = parseInt(b.quantity, 10) || 0;
    return qa - qb;
  }
  