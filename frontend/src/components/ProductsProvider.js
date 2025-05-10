import React, { createContext, useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import { getProducts } from '../services/api';  // теперь корректно импортируется

export const ProductsContext = createContext();

function ProductsProvider({ children }) {
  const [products, setProducts]       = useState([]);
  const [loading, setLoading]         = useState(false);
  const [error, setError]             = useState(null);
  const [lastRunTime, setLastRunTime] = useState(null);

  const fetchProducts = async () => {
    setLoading(true);
    try {
      const data = await getProducts();   // возвращает уже res.data
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
