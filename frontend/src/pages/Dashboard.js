import React, { useContext } from 'react';
import { ProductsContext } from '../components/ProductsProvider';
import ProductCard from '../components/ProductCard';

function Dashboard() {
  const { products, loading, error } = useContext(ProductsContext);

  // Если данные ещё загружаются – показываем индикатор загрузки
  if (loading) {
    return <p>Загрузка данных...</p>;
  }

  // Если при загрузке произошла ошибка – отображаем сообщение об ошибке
  if (error) {
    return <p className="text-red-600">Ошибка загрузки: {error.message || 'Неизвестная ошибка'}</p>;
  }

  // Рассчитываем основные метрики для отображения на дашборде
  const totalProducts = products.length;
  const totalCategories = new Set(products.map(p => p.category)).size;
  const totalMarketplaces = new Set(products.map(p => p.marketplace)).size;

  // Сортируем продукты по текущим продажам для определения топ-5
  const topProducts = [...products].sort((a, b) => {
    const salesA = a.currentSales || 0;
    const salesB = b.currentSales || 0;
    return salesB - salesA;
  }).slice(0, 5);  // берем первые 5 товаров

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Обзор активности</h1>
      {/* Блок основных метрик */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-white shadow p-4 rounded">
          <p className="text-gray-600">Всего товаров</p>
          <p className="text-2xl font-bold">{totalProducts}</p>
        </div>
        <div className="bg-white shadow p-4 rounded">
          <p className="text-gray-600">Категорий</p>
          <p className="text-2xl font-bold">{totalCategories}</p>
        </div>
        <div className="bg-white shadow p-4 rounded">
          <p className="text-gray-600">Маркетплейсов</p>
          <p className="text-2xl font-bold">{totalMarketplaces}</p>
        </div>
      </div>
      {/* Список топ-5 товаров по продажам */}
      <h2 className="text-xl font-semibold mb-3">Топ товары</h2>
      {topProducts.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {topProducts.map(product => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : (
        <p>Данные о товарах отсутствуют.</p>
      )}
    </div>
  );
}

export default Dashboard;
