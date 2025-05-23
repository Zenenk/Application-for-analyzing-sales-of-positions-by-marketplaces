// frontend/src/pages/Dashboard.jsx
import React, { useEffect, useState } from 'react';
import API from '../services/api';
import { useNavigate } from 'react-router-dom';

// === HELPERS для градиентных цветов ===
// diff: отрицательное — падение (зелёный), положительное — рост (красный)
const getPriceColor = diff => {
  const capped = Math.max(-500, Math.min(500, diff));
  // нормируем в [0..1], где -500 → 1 (зелёный), 0 → 0.5 (серый), +500 → 0 (красный)
  const t = 1 - (capped + 500) / 1000;
  const r = Math.round(200 - 150 * t);    // от 200 до 50
  const g = Math.round(50 + 150 * t);     // от 50 до 200
  return `rgb(${r},${g},50)`;
};

// pct: от 0 до 80
const getDiscountColor = pct => {
  const p = Math.max(0, Math.min(80, pct)) / 80;
  // серый(150,150,150) → тёмно-зелёный(0,100,0)
  const r = Math.round(150 * (1 - p));
  const g = Math.round(150 * (1 - p) + 100 * p);
  const b = Math.round(150 * (1 - p));
  return `rgb(${r},${g},${b})`;
};

// qty: чем ближе к 100, тем светлее (серый → почти белый)
const getQtyColor = qty => {
  const p = Math.min(qty, 100) / 100;
  const v = Math.round(50 + 100 * p); // от 50 до 150
  return `rgb(${v},${v},${v})`;
};

function Dashboard() {
  const navigate = useNavigate();
  const [loading, setLoading]       = useState(true);
  const [error, setError]           = useState(null);
  const [metrics, setMetrics]       = useState({
    totalRecords: 0,
    uniqueCategories: 0,
    uniqueMarketplaces: 0
  });
  const [comparisons, setComparisons] = useState([]);

  useEffect(() => {
    async function fetchDashboard() {
      try {
        const prods = await API.getProductList();

        // Метрики
        setMetrics({
          totalRecords: prods.length,
          uniqueCategories: new Set(prods.map(p => p.category)).size,
          uniqueMarketplaces: new Set(prods.map(p => p.marketplace)).size
        });

        // Собираем сравнения по артикулу
        const sorted = [...prods].sort(
          (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
        );
        const seen = new Set();
        const compArr = [];
        

        for (const rec of sorted) {
          if (seen.has(rec.article)) continue;
          seen.add(rec.article);

          const hist = prods
            .filter(p => p.article === rec.article)
            .sort((a, b) => new Date(b.parsed_at).getTime() - new Date(a.parsed_at).getTime());

          if (hist.length >= 2) {
            const [newRec, oldRec] = hist;
            const oldPrice = parseFloat(oldRec.price) || 0;
            const newPrice = parseFloat(newRec.price) || 0;
            const priceDiff = Math.round((newPrice - oldPrice) * 100) / 100;

            const oldQty = oldRec.quantity !== '' ? parseInt(oldRec.quantity, 10) : null;
            const newQty = newRec.quantity !== '' ? parseInt(newRec.quantity, 10) : null;
            const qtyDiff = (oldQty != null && newQty != null) ? newQty - oldQty : null;

            const oldDisc = parseFloat(oldRec.discount) || 0;
            const newDisc = parseFloat(newRec.discount) || 0;
            const discountDiff = Math.round((newDisc - oldDisc) * 100) / 100;
            
            console.log(
              "[DBG image]", 
              rec.article,
              "old→", oldRec.image_url,
              "new→", newRec.image_url,
              "changed?", oldRec.image_url !== newRec.image_url
            );

            compArr.push({
              id: rec.id,
              article: rec.article,
              name:    newRec.name || rec.article,
              oldPrice, newPrice, priceDiff,
              oldQty, newQty, qtyDiff,
              oldDisc, newDisc, discountDiff,
              oldImage: oldRec.image_url,
              newImage: newRec.image_url,
              imageChanged: oldRec.image_url !== newRec.image_url,
              dateOld: oldRec.parsed_at,
              dateNew: newRec.parsed_at
            });
          }
        }

        // Оставляем только ненулевые изменения
        setComparisons(
          compArr.filter(item =>
            item.priceDiff !== 0 ||
            (item.qtyDiff != null && item.qtyDiff !== 0) ||
            item.discountDiff !== 0 ||
            item.imageChanged
          )
        );
      } catch (err) {
        console.error(err);
        setError('Не удалось загрузить данные дашборда');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) return <div className="dashboard-loading">Загрузка...</div>;
  if (error)   return <div className="dashboard-error text-red-600">{error}</div>;

  return (
    <div className="dashboard p-4">
      <h1 className="text-2xl font-bold mb-6">Обзор</h1>

      {/* Метрики */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="p-4 bg-white shadow rounded">
          <h2 className="text-lg font-semibold mb-2">Всего записей</h2>
          <p className="text-3xl">{metrics.totalRecords}</p>
        </div>
        <div className="p-4 bg-white shadow rounded">
          <h2 className="text-lg font-semibold mb-2">Категорий</h2>
          <p className="text-3xl">{metrics.uniqueCategories}</p>
        </div>
        <div className="p-4 bg-white shadow rounded">
          <h2 className="text-lg font-semibold mb-2">Маркетплейсов</h2>
          <p className="text-3xl">{metrics.uniqueMarketplaces}</p>
        </div>
      </div>

      {/* Изменения */}
      <h2 className="text-xl font-semibold mb-4">Изменения товаров</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-4 py-2 text-center">Картинка</th>
              <th className="px-4 py-2 text-left">Товар</th>
              <th className="px-4 py-2 text-left">Период</th>
              <th className="px-4 py-2 text-right">Старая → Новая цена</th>
              <th className="px-4 py-2 text-right">Δ Цена</th>
              <th className="px-4 py-2 text-right">Скидка</th>
              <th className="px-4 py-2 text-right">Старый → Новый остаток</th>
              <th className="px-4 py-2 text-right">Δ Остатка</th>
            </tr>
          </thead>
          <tbody>
            {comparisons.map(item => (
              <tr key={`${item.article}-${item.dateNew}`} className="border-t cursor-pointer hover:bg-gray-50" onClick={() => navigate(`/product/${item.id}`)}>
                <td className="px-4 py-2 text-center">
                  {item.imageChanged
                    ? <span className="text-red-600">Изменилась ({item.article})</span>
                    : <span className="text-gray-400">ОК ({item.article})</span>
                  }
                </td>
                <td className="px-4 py-2">{item.name}</td>
                <td className="px-4 py-2">
                  {item.dateOld && new Date(item.dateOld).toLocaleString()}<br/>
                  {item.dateNew && new Date(item.dateNew).toLocaleString()}
                </td>
                <td className="px-4 py-2 text-right">
                  {item.oldPrice} → {item.newPrice}
                </td>
                <td
                  className="px-4 py-2 text-right"
                  style={{ color: getPriceColor(item.priceDiff) }}
                >
                  {item.priceDiff >= 0 ? `+${item.priceDiff}` : item.priceDiff}
                </td>
                <td
                  className="px-4 py-2 text-right"
                  style={{ color: getDiscountColor(item.newDisc) }}
                >
                  {item.newDisc}% ({item.discountDiff >= 0 ? `+${item.discountDiff}` : item.discountDiff})
                </td>
                <td className="px-4 py-2 text-right">
                  {item.oldQty ?? '—'} → {item.newQty ?? '—'}
                </td>
                <td
                  className="px-4 py-2 text-right"
                  style={{ color: getQtyColor(item.newQty || 0) }}
                >
                  {item.qtyDiff != null
                    ? (item.qtyDiff >= 0 ? `+${item.qtyDiff}` : item.qtyDiff)
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Dashboard;
