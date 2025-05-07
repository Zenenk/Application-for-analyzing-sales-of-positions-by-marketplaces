import React, { useContext, useState } from 'react';
import { ProductsContext } from '../components/ProductsProvider';
import ProductCard from '../components/ProductCard';

function ProductList() {
  const { products, loading, error } = useContext(ProductsContext);

  // Локальное состояние фильтров: категория, маркетплейс, артикул
  const [categoryFilter, setCategoryFilter] = useState('');
  const [marketplaceFilter, setMarketplaceFilter] = useState('');
  const [articleFilter, setArticleFilter] = useState('');

  // Обработчики изменений фильтров
  const handleCategoryChange = (e) => setCategoryFilter(e.target.value);
  const handleMarketplaceChange = (e) => setMarketplaceFilter(e.target.value);
  const handleArticleChange = (e) => setArticleFilter(e.target.value);

  // Формирование списка отфильтрованных товаров на основе выбранных фильтров
  const filteredProducts = products.filter(product => {
    const matchCategory = categoryFilter === '' || product.category === categoryFilter;
    const matchMarketplace = marketplaceFilter === '' || product.marketplace === marketplaceFilter;
    const matchArticle = articleFilter === '' || product.article.toLowerCase().includes(articleFilter.toLowerCase());
    return matchCategory && matchMarketplace && matchArticle;
  });

  // Получение списков уникальных категорий и маркетплейсов для заполнения выпадающих списков фильтров
  const categories = Array.from(new Set(products.map(p => p.category)));
  const marketplaces = Array.from(new Set(products.map(p => p.marketplace)));

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Список товаров</h1>
      
      {/* Форма фильтрации */}
      <div className="bg-white p-4 rounded shadow mb-6">
        <div className="flex flex-col md:flex-row md:items-end md:space-x-4">
          {/* Фильтр по категории */}
          <div className="mb-4 md:mb-0">
            <label htmlFor="category" className="block text-sm font-medium text-gray-700">Категория</label>
            <select 
              id="category" 
              value={categoryFilter} 
              onChange={handleCategoryChange} 
              className="mt-1 block w-full border-gray-300 rounded"
            >
              <option value="">Все категории</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          {/* Фильтр по маркетплейсу */}
          <div className="mb-4 md:mb-0">
            <label htmlFor="marketplace" className="block text-sm font-medium text-gray-700">Маркетплейс</label>
            <select 
              id="marketplace" 
              value={marketplaceFilter} 
              onChange={handleMarketplaceChange} 
              className="mt-1 block w-full border-gray-300 rounded"
            >
              <option value="">Все маркетплейсы</option>
              {marketplaces.map(mp => (
                <option key={mp} value={mp}>{mp}</option>
              ))}
            </select>
          </div>
          {/* Фильтр по артикулу */}
          <div>
            <label htmlFor="article" className="block text-sm font-medium text-gray-700">Артикул</label>
            <input 
              id="article" 
              type="text" 
              value={articleFilter} 
              onChange={handleArticleChange} 
              placeholder="Поиск по артикулу..." 
              className="mt-1 block w-full border-gray-300 rounded"
            />
          </div>
        </div>
      </div>

      {/* Блок состояния загрузки/ошибки */}
      {loading && <p>Загрузка товаров...</p>}
      {error && <p className="text-red-600">Ошибка: {error.message}</p>}

      {/* Список карточек товаров после применения фильтров */}
      {filteredProducts.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredProducts.map(product => (
            <ProductCard key={product.id} product={product} />
          ))}
        </div>
      ) : (
        !loading && <p>Товары не найдены.</p>
      )}
    </div>
  );
}

export default ProductList;
