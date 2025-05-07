import React, { useContext } from 'react';
import { useParams } from 'react-router-dom';
import { ProductsContext } from '../components/ProductsProvider';
// Импорт компонентов Recharts для построения графика
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function ProductDetails() {
  const { id } = useParams();                   // Получаем ID товара из URL параметра
  const { products } = useContext(ProductsContext);
  const product = products.find(p => String(p.id) === id);  // Ищем товар по идентификатору среди загруженных

  if (!product) {
    // Если товар с данным ID не найден (например, данные ещё не загружены или неверный ID)
    return <p>Товар не найден.</p>;
  }

  // Деструктурируем данные товара для удобства
  const { name, category, marketplace, article, currentSales, previousSales, history, image } = product;

  // Вычисляем изменение продаж в процентах между текущим и предыдущим периодами
  let changePercent = null;
  if (currentSales != null && previousSales != null) {
    if (previousSales === 0) {
      changePercent = previousSales === 0 ? '∞%' : '0%';
    } else {
      const diff = currentSales - previousSales;
      changePercent = ((diff / previousSales) * 100).toFixed(1) + '%';
    }
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Детали товара: {name}</h1>
      {/* Общая информация о товаре */}
      <div className="bg-white p-4 rounded shadow mb-4">
        {/* Изображение товара */}
        {image && (
          <img src={image} alt={name} className="h-48 object-contain mb-4" />
        )}
        <p><strong>Категория:</strong> {category}</p>
        <p><strong>Маркетплейс:</strong> {marketplace}</p>
        <p><strong>Артикул:</strong> {article}</p>
        {/* Блок текущих и предыдущих продаж и изменения */}
        {currentSales != null && (
          <p>
            <strong>Текущие продажи:</strong> {currentSales} <br />
            {previousSales != null && (
              <>
                <strong>Предыдущие продажи:</strong> {previousSales} <br />
              </>
            )}
            {changePercent !== null && (
              <span className={currentSales >= (previousSales || 0) ? 'text-green-600' : 'text-red-600'}>
                Изменение: {currentSales >= (previousSales || 0) ? '▲' : '▼'} {changePercent}
              </span>
            )}
          </p>
        )}
      </div>
      {/* График динамики продаж */}
      {history && history.length > 0 && (
        <div className="bg-white p-4 rounded shadow">
          <h2 className="text-xl font-semibold mb-2">Динамика продаж</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={history}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="sales" stroke="#8884d8" name="Продажи" />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}

export default ProductDetails;
