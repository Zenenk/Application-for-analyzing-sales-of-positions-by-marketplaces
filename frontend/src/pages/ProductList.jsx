import React, { useEffect, useState } from 'react';
import API from '../services/api';

function ProductList() {
  const [products, setProducts] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Получаем список продуктов при монтировании
    API.getProductList()
      .then((productsData) => {
        setProducts(productsData);
      })
      .catch((err) => {
        console.error('Error fetching product list:', err);
        setError('Не удалось загрузить список продуктов');
      });
  }, []);

  if (error) {
    return <div className="product-error">{error}</div>;
  }

  if (!products) {
    return <div className="product-loading">Загрузка товаров...</div>;
  }

  return (
    <div className="product-list">
      <h1>Product List</h1>
      {/* Отображаем продукты, если получили массив */}
      {Array.isArray(products) ? (
        <ul>
          {products.map((product, index) => (
            <li key={product.id || index}>
              {product.name || product.title || `Product ${index + 1}`}
            </li>
          ))}
        </ul>
      ) : (
        // Если данные не являются массивом (например, объект с подробностями)
        <pre>{JSON.stringify(products, null, 2)}</pre>
      )}
    </div>
  );
}

export default ProductList;
