// frontend/src/pages/ProductDetails.jsx
import React, { useContext, useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import API from '../services/api';
import { ProductsContext } from '../components/ProductsProvider';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const ProductDetails = () => {
  const { id } = useParams();
  const { products } = useContext(ProductsContext);
  const product = products.find(p => p.id === Number(id));

  const [historyData, setHistoryData] = useState([]);
  const [historyError, setHistoryError] = useState(null);

  useEffect(() => {
    if (!product) return;
    API.getProductHistory(product.article)
      .then(data => setHistoryData(data))
      .catch(err => {
        console.error('Error fetching history:', err);
        setHistoryError('Не удалось загрузить историю');
      });
  }, [product]);

  if (!product) {
    return <p>Товар не найден.</p>;
  }

  const {
    name,
    article,
    image_url,
    category,
    marketplace,
    price_old,
    price_new,
    discount,
    promo_labels,
    currentSales,
    previousSales
  } = product;

  let changePercent = null;
  if (currentSales != null && previousSales != null) {
    if (previousSales === 0 && currentSales > 0) {
      changePercent = '∞%';
    } else if (previousSales !== 0) {
      const diff = ((currentSales - previousSales) / previousSales) * 100;
      changePercent = `${diff.toFixed(0)}%`;
    }
  }

  const renderPromoDuration = () => {
    const indices = historyData
      .map((h, i) => ({ idx: i, val: parseFloat(h.discount) || 0 }))
      .filter(item => item.val > 0)
      .map(item => item.idx);
    if (indices.length === 0) return null;
    const startDate = new Date(historyData[indices[0]].parsed_at);
    const endDate = new Date(historyData[indices[indices.length - 1]].parsed_at);
    const days = Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24)) + 1;
    return (
      <p className="mt-2">
        Акция длится уже {days} {days === 1 ? 'день' : 'дня'}.
      </p>
    );
  };

  return (
    <div className="p-4 space-y-6">
      <h2 className="text-2xl font-bold">{name}</h2>
      {image_url && (
        <img src={image_url} alt={name} className="w-1/2 rounded" />
      )}
      <p>Артикул: {article}</p>
      {category && <p>Категория: {category}</p>}
      {marketplace && <p>Маркетплейс: {marketplace}</p>}

      {price_old && (
        <p className="line-through text-gray-500">Старая цена: {price_old}</p>
      )}
      {price_new && (
        <p className="text-red-600 font-semibold">Новая цена: {price_new}</p>
      )}
      {discount && <p className="text-green-600">Скидка: {discount}</p>}
      {promo_labels && promo_labels.length > 0 && (
        <p>Промо-лейблы: {promo_labels.join(', ')}</p>
      )}

      {currentSales != null && (
        <div>
          <p>Продажи (текущие): {currentSales}</p>
          {changePercent != null && (
            <p
              className={
                currentSales >= previousSales ? 'text-green-600' : 'text-red-600'
              }
            >
              Изменение: {changePercent}
            </p>
          )}
        </div>
      )}

      {historyError && <div className="text-red-600">{historyError}</div>}

      {historyData.length > 0 && (
        <div className="space-y-8">
          {['price', 'discount', 'quantity'].map((key, idx) => (
            <div key={key}>
              <h3 className="font-semibold mb-2">
                {key === 'price'
                  ? 'Динамика цены'
                  : key === 'discount'
                  ? 'Динамика скидки'
                  : 'Динамика остатков'}
              </h3>
              <div style={{ width: '100%', height: 250 }}>
                <ResponsiveContainer>
                  <LineChart data={historyData}>
                    <XAxis dataKey="parsed_at" />
                    <YAxis />
                    <Tooltip />
                    <Line
                      type="monotone"
                      dataKey={key}
                      name={
                        key === 'price'
                          ? 'Цена'
                          : key === 'discount'
                          ? 'Скидка'
                          : 'Остаток'
                      }
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          ))}
          {renderPromoDuration()}
          <button
            onClick={() => {
              window.open(
                `/api/export/product/${encodeURIComponent(article)}`,
                '_blank'
              );
            }}
            className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
          >
            Экспорт PDF с инфографикой
          </button>
        </div>
      )}
    </div>
  );
};

export default ProductDetails;