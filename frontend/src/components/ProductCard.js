import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';

// Компонент карточки товара для отображения в списках (Dashboard, ProductList)
function ProductCard({ product }) {
  // Вычисляем процент изменения продаж (динамика) между текущим и предыдущим периодом
  const { id, name, category, marketplace, article, currentSales, previousSales, image } = product;
  let changePercent = null;
  if (currentSales != null && previousSales != null) {
    if (previousSales === 0) {
      // Если ранее продаж не было (0), то изменение на 100% (или бесконечный рост)
      changePercent = previousSales === 0 ? '∞%' : '0%';
    } else {
      const diff = currentSales - previousSales;
      changePercent = ((diff / previousSales) * 100).toFixed(1) + '%';
    }
  }

  return (
    <div className="bg-white shadow rounded p-4 flex flex-col">
      {/* Изображение товара (если есть). Ограничиваем высоту, чтобы карточки были компактными */}
      {image ? (
        <img src={image} alt={name} className="h-32 object-contain mb-2 self-center" />
      ) : (
        <div className="h-32 flex items-center justify-center bg-gray-100 text-gray-500 mb-2">
          Нет изображения
        </div>
      )}
      {/* Название товара как ссылка на страницу деталей */}
      <h3 className="font-bold text-lg mb-1">
        <Link to={`/product/${id}`} className="text-blue-600 hover:underline">
          {name}
        </Link>
      </h3>
      {/* Категория и маркетплейс */}
      <p className="text-sm text-gray-700 mb-1">Категория: <strong>{category}</strong></p>
      <p className="text-sm text-gray-700 mb-2">Маркетплейс: <strong>{marketplace}</strong></p>
      {/* Артикул товара */}
      <p className="text-sm text-gray-500 mb-2">Артикул: {article}</p>
      {/* Текущие продажи и изменение (если доступно) */}
      {currentSales != null && (
        <p className="text-sm">
          Продажи: <strong>{currentSales}</strong>
          {changePercent !== null && (
            <span className={`ml-2 ${currentSales >= previousSales ? 'text-green-600' : 'text-red-600'}`}>
              ({currentSales >= previousSales ? '▲' : '▼'} {changePercent})
            </span>
          )}
        </p>
      )}
    </div>
  );
}

ProductCard.propTypes = {
  // Ожидаем объект товара с указанными полями
  product: PropTypes.shape({
    id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
    name: PropTypes.string.isRequired,
    category: PropTypes.string.isRequired,
    marketplace: PropTypes.string.isRequired,
    article: PropTypes.string.isRequired,
    currentSales: PropTypes.number,    // может быть null, если данных нет
    previousSales: PropTypes.number,   // может быть null
    image: PropTypes.string,           // URL изображения товара
    history: PropTypes.arrayOf(PropTypes.shape({
      date: PropTypes.string.isRequired,
      sales: PropTypes.number.isRequired
    }))
  }).isRequired
};

export default ProductCard;
