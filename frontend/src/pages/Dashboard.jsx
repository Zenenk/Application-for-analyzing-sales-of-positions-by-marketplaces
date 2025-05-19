// frontend/src/pages/Dashboard.jsx
import React, { useEffect, useState } from 'react';
import API from '../services/api';

function Dashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [metrics, setMetrics] = useState({
    totalRecords: 0,
    uniqueCategories: 0,
    uniqueMarketplaces: 0
  });
  const [comparisons, setComparisons] = useState([]);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        // 1) Получаем все записи о товарах
        const prods = await API.getProductList();

        // 2) Вычисляем основные метрики
        const totalRecords       = prods.length;
        const uniqueCategories   = new Set(prods.map(p => p.category)).size;
        const uniqueMarketplaces = new Set(prods.map(p => p.marketplace)).size;
        setMetrics({ totalRecords, uniqueCategories, uniqueMarketplaces });

        // 3) Группируем по артикулу и берём 10 последних изменений
        const sortedRecords = [...prods].sort(
          (a, b) => new Date(b.timestamp) - new Date(a.timestamp)
        );
        const seen    = new Set();
        const compArr = [];

        for (const record of sortedRecords) {
          const article = record.article;
          if (!article || seen.has(article)) continue;
          seen.add(article);

          // История по данному артикулу
          const history = prods
            .filter(p => p.article === article)
            .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

          if (history.length >= 2) {
            const [newRec, oldRec] = history;

            // Парсим числа и считаем разницы
            const oldPrice = parseFloat(oldRec.price) || 0;
            const newPrice = parseFloat(newRec.price) || 0;
            const priceDiff = Math.round((newPrice - oldPrice) * 100) / 100;

            const oldQty = oldRec.quantity !== '' ? parseInt(oldRec.quantity, 10) : null;
            const newQty = newRec.quantity !== ''   ? parseInt(newRec.quantity, 10) : null;
            const qtyDiff =
              oldQty != null && newQty != null
                ? newQty - oldQty
                : null;

            compArr.push({
              article,
              name:     newRec.name || article,
              oldPrice: oldRec.price,
              newPrice: newRec.price,
              priceDiff,
              oldQty,
              newQty,
              qtyDiff,
              dateOld: oldRec.parsed_at,
              dateNew: newRec.parsed_at
            });
          }

          if (compArr.length >= 10) break;
        }

        setComparisons(compArr);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
        setError('Не удалось загрузить данные дашборда');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboard();
  }, []);

  if (loading) {
    return <div className="dashboard-loading">Загрузка...</div>;
  }

  if (error) {
    return <div className="dashboard-error text-red-600">{error}</div>;
  }

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

      {/* Список сравнений */}
      <h2 className="text-xl font-semibold mb-4">Последние изменения товаров</h2>
      <div className="overflow-x-auto">
        <table className="min-w-full bg-white border border-gray-200">
          <thead>
            <tr className="bg-gray-100">
              <th className="px-4 py-2 text-left">Товар</th>
              <th className="px-4 py-2 text-left">Период</th>
              <th className="px-4 py-2 text-right">Цена (старое → новое)</th>
              <th className="px-4 py-2 text-right">Δ Цена</th>
              <th className="px-4 py-2 text-right">Остаток (старое → новое)</th>
              <th className="px-4 py-2 text-right">Δ Остатка</th>
            </tr>
          </thead>
          <tbody>
            {comparisons.map(item => (
              <tr key={item.article} className="border-t">
                <td className="px-4 py-2">{item.name}</td>
                <td className="px-4 py-2">
                  {item.dateOld
                    ? new Date(item.dateOld).toLocaleString()
                    : '—'}
                  <br />
                  {item.dateNew
                    ? new Date(item.dateNew).toLocaleString()
                    : '—'}
                </td>
                <td className="px-4 py-2 text-right">
                  {item.oldPrice} → {item.newPrice}
                </td>
                <td
                  className={`px-4 py-2 text-right ${
                    item.priceDiff >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {item.priceDiff >= 0 ? `+${item.priceDiff}` : item.priceDiff}
                </td>
                <td className="px-4 py-2 text-right">
                  {item.oldQty != null ? item.oldQty : '—'} → 
                  {item.newQty != null ? item.newQty : '—'}
                </td>
                <td
                  className={`px-4 py-2 text-right ${
                    item.qtyDiff != null && item.qtyDiff >= 0
                      ? 'text-green-600'
                      : 'text-red-600'
                  }`}
                >
                  {item.qtyDiff != null
                    ? item.qtyDiff >= 0
                      ? `+${item.qtyDiff}`
                      : item.qtyDiff
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
