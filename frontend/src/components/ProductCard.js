// frontend/src/components/ProductCard.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';

const ProductCard = ({ product }) => {
  const {
    id,
    name,
    article,
    image_url,
    currentSales,
    previousSales,
    category,
    marketplace,
    price_old,
    price_new,
    discount,
    promo_labels,
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

  return (
    <div className="border rounded p-4 hover:shadow-lg">
      {image_url ? (
        <img src={image_url} alt={name} className="w-full h-48 object-cover" />
      ) : (
        <div className="w-full h-48 bg-gray-200 flex items-center justify-center">
          Нет изображения
        </div>
      )}
      <h3 className="mt-2 text-lg font-semibold">
        <Link to={`/product/${id}`}>{name}</Link>
      </h3>
      <p>Артикул: {article}</p>
      {category && <p>Категория: {category}</p>}
      {marketplace && <p>Маркетплейс: {marketplace}</p>}

      {/* Новые поля скидок */}
      {price_old && (
        <p className="line-through text-gray-400">
          Старая цена: {price_old}
        </p>
      )}
      {price_new && (
        <p className="text-red-600 font-bold">
          Новая цена: {price_new}
        </p>
      )}
      {discount && (
        <p className="text-green-600">Скидка: {discount}</p>
      )}
      {promo_labels && promo_labels.length > 0 && (
        <p>Промо: {promo_labels.join(', ')}</p>
      )}

      {/* Блок продаж */}
      {changePercent != null && (
        <div className="mt-2">
          <p>Продажи: {currentSales}</p>
          <p className={currentSales >= previousSales ? 'text-green-600' : 'text-red-600'}>
            {changePercent}
          </p>
        </div>
      )}
    </div>
  );
};

ProductCard.propTypes = {
  product: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string.isRequired,
    article: PropTypes.string.isRequired,
    image_url: PropTypes.string,
    currentSales: PropTypes.number,
    previousSales: PropTypes.number,
    category: PropTypes.string,
    marketplace: PropTypes.string,
    price_old: PropTypes.string,
    price_new: PropTypes.string,
    discount: PropTypes.string,
    promo_labels: PropTypes.arrayOf(PropTypes.string),
  }).isRequired,
};

export default ProductCard;

