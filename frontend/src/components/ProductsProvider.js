import React, { createContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getProducts } from '../services/api';

// Создаём контекст для продуктов
export const ProductsContext = createContext();

// Провайдер продуктов, который хранит глобальный список товаров и состояние загрузки/ошибки
function ProductsProvider({ children }) {
  const [products, setProducts] = useState([]);       // Список товаров, полученных из API
  const [loading, setLoading] = useState(false);      // Флаг загрузки данных
  const [error, setError] = useState(null);           // Состояние ошибки при загрузке
  const [lastRunTime, setLastRunTime] = useState(null); // Время последнего запуска анализа

  // Функция для загрузки продуктов с сервера
  const fetchProducts = async () => {
    setLoading(true);
    try {
      // Выполняем GET запрос к /api/products
      const response = await getProducts();
      setProducts(response.data || []);  // Обновляем список продуктов
      setError(null);
    } catch (err) {
      // В случае ошибки сохраняем объект ошибки (для отображения сообщения)
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  // Загружаем продукты один раз при монтировании провайдера
  useEffect(() => {
    fetchProducts();
  }, []);

  // Контекстное значение, доступное в дочерних компонентах через useContext(ProductsContext)
  const contextValue = {
    products,
    loading,
    error,
    lastRunTime,
    setLastRunTime,
    refresh: fetchProducts  // Метод для повторной загрузки данных
  };

  return (
    <ProductsContext.Provider value={contextValue}>
      {children}
    </ProductsContext.Provider>
  );
}

ProductsProvider.propTypes = {
  // Провайдер ожидает на вход дочерние элементы React
  children: PropTypes.node.isRequired
};

export default ProductsProvider;
