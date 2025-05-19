import React, { useContext, useState, useMemo } from 'react';
import { ProductsContext } from '../components/ProductsProvider';
import ProductCard from '../components/ProductCard';

export default function ProductList() {
  const { products = [], loading, error } = useContext(ProductsContext);

  // Фильтрующие состояния
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo]     = useState('');
  const [selectedCategories, setSelectedCategories]     = useState([]);
  const [selectedMarketplaces, setSelectedMarketplaces] = useState([]);
  const [priceMin, setPriceMin] = useState('');
  const [priceMax, setPriceMax] = useState('');

  // Динамически извлекаем варианты из загруженных продуктов
  const categoriesList = useMemo(
    () => Array.from(new Set(products.map(p => p.category).filter(Boolean))),
    [products]
  );
  const marketplacesList = useMemo(
    () => Array.from(new Set(products.map(p => p.marketplace).filter(Boolean))),
    [products]
  );

  // Фильтрация
  const filteredProducts = useMemo(() => {
    return products
      .filter(p => {
        if (dateFrom) {
          const d = p.parsed_at?.slice(0, 10) || '';
          if (d < dateFrom) return false;
        }
        if (dateTo) {
          const d = p.parsed_at?.slice(0, 10) || '';
          if (d > dateTo) return false;
        }
        return true;
      })
      .filter(p => {
        if (selectedCategories.length) {
          return selectedCategories.includes(p.category);
        }
        return true;
      })
      .filter(p => {
        if (selectedMarketplaces.length) {
          return selectedMarketplaces.includes(p.marketplace);
        }
        return true;
      })
      .filter(p => {
        const price = parseFloat(p.price) || 0;
        if (priceMin && price < parseFloat(priceMin)) return false;
        if (priceMax && price > parseFloat(priceMax)) return false;
        return true;
      });
  }, [products, dateFrom, dateTo, selectedCategories, selectedMarketplaces, priceMin, priceMax]);

  // Статистика
  const today = new Date().toISOString().slice(0, 10);
  const dailyCount = useMemo(
    () => products.filter(p => p.parsed_at?.startsWith(today)).length,
    [products, today]
  );
  const promoCount = useMemo(
    () => filteredProducts.filter(p => p.promotion_detected).length,
    [filteredProducts]
  );
  const nonPromoCount = filteredProducts.length - promoCount;

  // Группировка
  const groupedByCategory = useMemo(() => {
    return filteredProducts.reduce((acc, p) => {
      const key = p.category || 'Без категории';
      (acc[key] || (acc[key] = [])).push(p);
      return acc;
    }, {});
  }, [filteredProducts]);

  const isFiltered = dateFrom || dateTo || selectedCategories.length ||
    selectedMarketplaces.length || priceMin || priceMax;

  if (loading) return <div>Загрузка товаров...</div>;
  if (error)   return <div className="text-red-600">Ошибка: {error}</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Товары</h1>

      {/* Панель фильтров */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4 bg-white p-4 rounded shadow mb-6">
        <div>
          <label className="block text-sm">Дата от</label>
          <input type="date" className="mt-1 w-full border rounded"
            value={dateFrom} onChange={e => setDateFrom(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm">Дата до</label>
          <input type="date" className="mt-1 w-full border rounded"
            value={dateTo} onChange={e => setDateTo(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm">Категории</label>
          <select multiple size={4} className="mt-1 w-full border rounded"
            value={selectedCategories}
            onChange={e => setSelectedCategories(
              Array.from(e.target.selectedOptions, opt => opt.value)
            )}>
            {categoriesList.map(cat => <option key={cat} value={cat}>{cat}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm">Маркетплейсы</label>
          <select multiple size={4} className="mt-1 w-full border rounded"
            value={selectedMarketplaces}
            onChange={e => setSelectedMarketplaces(
              Array.from(e.target.selectedOptions, opt => opt.value)
            )}>
            {marketplacesList.map(mp => <option key={mp} value={mp}>{mp}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm">Цена ≥</label>
          <input type="number" className="mt-1 w-full border rounded"
            placeholder="мин" value={priceMin}
            onChange={e => setPriceMin(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm">Цена ≤</label>
          <input type="number" className="mt-1 w-full border rounded"
            placeholder="макс" value={priceMax}
            onChange={e => setPriceMax(e.target.value)} />
        </div>
      </div>

      {/* Статистика */}
      {isFiltered && (
        <div className="bg-white p-4 rounded shadow mb-6 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>Запросов сегодня: <strong>{dailyCount}</strong></div>
          <div>Промо: <strong>{promoCount}</strong></div>
          <div>Не промо: <strong>{nonPromoCount}</strong></div>
        </div>
      )}

      {/* Результаты */}
      {!isFiltered ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {products.map(p => (
            <ProductCard key={`${p.timestamp}-${p.article}`} product={p} />
          ))}
        </div>
      ) : (
        Object.entries(groupedByCategory).map(([cat, items]) => (
          <div key={cat} className="mb-8">
            <h2 className="text-xl font-semibold mb-2">{cat}</h2>
            <div className="overflow-x-auto">
              <table className="min-w-full bg-white border">
                <thead>
                  <tr className="bg-gray-100">
                    <th className="px-4 py-2 text-left">Артикул</th>
                    <th className="px-4 py-2 text-left">Название</th>
                    <th className="px-4 py-2 text-right">Цена</th>
                    <th className="px-4 py-2 text-right">Скидка</th>
                    <th className="px-4 py-2 text-left">Дата</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map(item => (
                    <tr key={`${item.timestamp}-${item.article}`} className="border-t">
                      <td className="px-4 py-2">{item.article}</td>
                      <td className="px-4 py-2">{item.name}</td>
                      <td className="px-4 py-2 text-right">{item.price}</td>
                      <td className="px-4 py-2 text-right">{item.discount || '—'}</td>
                      <td className="px-4 py-2">{new Date(item.parsed_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
