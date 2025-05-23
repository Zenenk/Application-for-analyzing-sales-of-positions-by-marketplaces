// frontend/src/pages/ProductDetails.jsx
import React, { useContext, useEffect, useState } from 'react';
import { useParams }                   from 'react-router-dom';
import API                             from '../services/api';
import { ProductsContext }            from '../components/ProductsProvider';
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

  // Ищем нашу запись по id
  const product = products.find(p => p.id === Number(id));

  const [historyData, setHistoryData] = useState([]);
  const [historyError, setHistoryError] = useState(null);

  useEffect(() => {
    if (!product) return;

    API.getProductHistory(product.article)
      .then(raw => {
        // raw — массив { parsed_at, price, price_old, price_new, discount, quantity }
          const parsed = raw
          .filter(item => item.parsed_at)
          .map(item => {
            // Берём ISO-строку, обрезаем лишние микросекунды, парсим в ms
            const cleaned = item.parsed_at.replace(/\.(\d{3})\d+/, '.$1');
            const ts = new Date(cleaned).getTime();
            const discountNum = parseFloat(
              item.discount
                ?.replace('−', '') 
                ?.replace('%', '')   // убираем %
                || 0
            ) || 0;
            console.log('→ discountNum:', discountNum);


            console.log('🛒 product:', product);
            return {
              parsed_at: ts,
              price:     parseFloat(item.price)      || 0,
              discount:  discountNum,
              quantity:  parseInt(item.quantity,10)  || 0,
              image_url: item.image_url,
            };
          })
          .sort((a, b) => a.parsed_at - b.parsed_at);
        console.log('📊 Chart data:', parsed);

        setHistoryData(parsed);
        setHistoryError(null);
      })
      .catch(err => {
        // 404 значит просто нет истории
        if (err.response?.status === 404) {
          setHistoryData([]);
          setHistoryError(null);
        } else {
          console.error('Error fetching history:', err);
          setHistoryError('Не удалось загрузить историю');
        }
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
    promo_labels
  } = product;

  // Рисуем только если хотя бы 2 точки
  const canPlot = historyData.length >= 2;
  const imageChanged = canPlot && historyData[0].image_url !== historyData[historyData.length - 1].image_url;

  return (
    <div className="p-4 space-y-6">
      <h2 className="text-2xl font-bold">{name}</h2>

      {image_url && (
        <img src={image_url} alt={name} className="w-1/2 rounded" />
      )}
      {/* Если картинка сменилась, показываем старую и новую */}
      {imageChanged && (
        <div className="mt-4">
          <p className="text-red-600 font-medium">Изображение изменилось</p>
          <div className="flex space-x-4 mt-2">
            <div>
              <p className="text-sm mb-1">Ранее:</p>
              <img
                src={historyData[0].image_url}
                alt="До"
                className="w-1/4 rounded"
              />
            </div>
            <div>
              <p className="text-sm mb-1">Теперь:</p>
              <img
                src={historyData[historyData.length - 1].image_url}
                alt="После"
                className="w-1/4 rounded"
              />
            </div>
          </div>
        </div>
      )}

      <p>Артикул: {article}</p>
      {category    && <p>Категория: {category}</p>}
      {marketplace && <p>Маркетплейс: {marketplace}</p>}

      {/* Цены и скидки */}
      {price_old && price_old !== price_new && (
        <p className="line-through text-gray-500">Старая цена: {price_old}</p>
      )}
      {price_new && (
        <p className="text-red-600 font-semibold">Новая цена: {price_new}</p>
      )}
      {(discount || discount === 0) && (
        <p className="text-green-600">Скидка: {discount}</p>
      )}
      {promo_labels?.length > 0 && (
        <p>Промо-лейблы: {promo_labels.join(', ')}</p>
      )}

      {/* Ошибка истории */}
      {historyError && (
        <div className="text-red-600">{historyError}</div>
      )}

      {canPlot ? (
        <div className="space-y-8">
          {['price', 'discount', 'quantity'].map(key => (
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
                    <XAxis
                      dataKey="parsed_at"
                      type="number"
                      scale="time"
                      domain={['dataMin','dataMax']}
                      tickFormatter={val =>
                        new Date(val).toLocaleDateString('ru-RU', {
                          day:   '2-digit',
                          month: '2-digit'
                        })
                      }
                    />
                    <YAxis />
                    <Tooltip
                      labelFormatter={val =>
                        new Date(val).toLocaleString('ru-RU', {
                          timeZone: 'Europe/Moscow',
                          hour12:   false,
                          year:     'numeric',
                          month:    '2-digit',
                          day:      '2-digit',
                          hour:     '2-digit',
                          minute:   '2-digit'
                        }) + ' МСК'
                      }
                    />
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
                      stroke="#3182ce"
                      strokeWidth={2}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
          ))}

          <button
            onClick={() => window.open(API.exportProductUrl(article), '_blank')}
            className="mt-4 bg-indigo-600 text-white px-4 py-2 rounded hover:bg-indigo-700"
          >
            Экспорт PDF с инфографикой
          </button>
        </div>
      ) : (
        <p>Данных для графиков пока нет.</p>
      )}
    </div>
  );
};

export default ProductDetails;
