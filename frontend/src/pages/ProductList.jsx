// frontend/src/pages/ProductList.jsx
import React, { useEffect, useState, useMemo } from 'react';
import API from '../services/api';
import ProductCard from '../components/ProductCard';
import { sortByHierarchy } from '../utils/sortProducts';
import { sortByHierarchy } from '../utils/sortProducts';

function ProductList() {
  const [products, setProducts] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    API.getProductList()
      .then(data => setProducts(data))
      .catch(err => {
        console.error('Error fetching product list:', err);
        setError('Не удалось загрузить список продуктов');
      });
  }, []);

  const sortedProducts = useMemo(() => {
    if (!products) return [];
    return [...products].sort(sortByHierarchy);
  }, [products]);

  if (error) return <div className="text-red-600">{error}</div>;
  if (!products) return <div>Загрузка товаров...</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {sortedProducts.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}

export default ProductList;
