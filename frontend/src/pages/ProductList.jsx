import React, { useEffect, useState } from 'react';
import API from '../services/api';
import ProductCard from '../components/ProductCard';

function ProductList() {
  const [products, setProducts] = useState(null);
  const [error, setError]       = useState(null);

  useEffect(() => {
    API.getProductList()
      .then(data => setProducts(data))
      .catch(err => {
        console.error('Error fetching product list:', err);
        setError('Не удалось загрузить список продуктов');
      });
  }, []);

  if (error)   return <div className="text-red-600">{error}</div>;
  if (!products) return <div>Загрузка товаров...</div>;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      {products.map(product => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}

export default ProductList;
