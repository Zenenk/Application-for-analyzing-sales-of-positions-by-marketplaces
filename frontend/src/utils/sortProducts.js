// frontend/src/utils/sortProducts.js

/**
 * Сортирует по иерархии:
 *   1) timestamp — новые записи первыми
 *   2) article   — по возрастанию (численно, если возможно)
 *   3) discount  — по убыванию (проценты)
 *   4) price     — по возрастанию
 *   5) quantity  — по возрастанию
 */
export function sortByHierarchy(a, b) {
  // 1) timestamp
  const ta = new Date(a.timestamp);
  const tb = new Date(b.timestamp);
  if (ta > tb) return -1;
  if (ta < tb) return 1;

  // 2) article
  const na = isNaN(+a.article) ? a.article : +a.article;
  const nb = isNaN(+b.article) ? b.article : +b.article;
  if (na < nb) return -1;
  if (na > nb) return 1;

  // 3) discount (строка "-15%")
  const da = parseFloat(String(a.discount).replace('%', '')) || 0;
  const db = parseFloat(String(b.discount).replace('%', '')) || 0;
  if (da > db) return -1;
  if (da < db) return 1;

  // 4) price (может быть строкой "123.45")
  const pa = parseFloat(String(a.price).replace(/[^0-9.]/g, '')) || 0;
  const pb = parseFloat(String(b.price).replace(/[^0-9.]/g, '')) || 0;
  if (pa < pb) return -1;
  if (pa > pb) return 1;

  // 5) quantity
  const qa = parseInt(a.quantity, 10) || 0;
  const qb = parseInt(b.quantity, 10) || 0;
  if (qa < qb) return -1;
  if (qa > qb) return 1;

  return 0;
}
