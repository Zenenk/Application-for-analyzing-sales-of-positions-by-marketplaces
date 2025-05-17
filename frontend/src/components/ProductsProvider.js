import React, { createContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import API from '../services/api';

export const ProductsContext = createContext();

function ProductsProvider({ children }) {
  const [products, setProducts]       = useState([]);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [lastRunTime, setLastRunTime] = useState(null);

  // Функция получения списка продуктов
  const fetchProducts = async () => {
    setLoading(true);
    try {
      const data = await API.getProductList();
      setProducts(Array.isArray(data) ? data : []);
      setError(null);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProducts();
  }, []);

  const contextValue = {
    products,
    loading,
    error,
    lastRunTime,
    setLastRunTime,
    refresh: fetchProducts
  };

  return (
    <ProductsContext.Provider value={contextValue}>
      {children}
    </ProductsContext.Provider>
  );
}

ProductsProvider.propTypes = {
  children: PropTypes.node.isRequired
};

export default ProductsProvider;
