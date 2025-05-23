// frontend/src/components/ProductCard.jsx
import React from 'react';
import PropTypes from 'prop-types';
import { Link } from 'react-router-dom';

const ProductCard = ({ product, filterCategory, filterMarketplace }) => {
  const {
    id,
    name,
    article,
    image_url,
    category: prodCategory,
    marketplace: prodMarketplace,
    price_old,
    price_new,
    discount,
    promo_labels,
    parsed_at
  } = product;

  // Используем фильтры, если у продукта нет своих значений
  const category = prodCategory || filterCategory;
  const marketplace = prodMarketplace || filterMarketplace;

  // Формат даты парсинга для отображения в карточке
  const parsedDate = parsed_at
    ? new Date(parsed_at).toLocaleString('ru-RU', {
        timeZone: 'Europe/Moscow', hour12: false,
        year: 'numeric', month: '2-digit', day: '2-digit',
        hour: '2-digit', minute: '2-digit'
      }) + ' МСК'
    : null;

  return (
    <div className="border rounded p-4 hover:shadow-lg bg-white">
      {image_url ? (
        <img src={image_url} alt={name} className="w-full h-48 object-cover" />
      ) : (
        <div className="w-full h-48 bg-gray-200 flex items-center justify-center text-gray-500">
          Нет изображения
        </div>
      )}
      <h3 className="mt-2 text-lg font-semibold">
        <Link to={`/product/${id}`}>{name}</Link>
      </h3>
      {product.image_changed && (
        <p className="text-red-600 mt-2">Изображение изменилось</p>
      )}
      <p className="text-sm text-gray-700">Артикул: {article}</p>
      {category && <p className="text-sm text-gray-600">Категория: {category}</p>}
      {marketplace && <p className="text-sm text-gray-600">Маркетплейс: {marketplace}</p>}

      {/* Цены и скидки */}
      {price_old && price_old !== price_new && (
        <p className="text-xs text-gray-500 line-through">
          Старая цена: {price_old}
        </p>
      )}
      {price_new && (
        <p className="text-sm text-red-600 font-bold">
          Новая цена: {price_new}
        </p>
      )}
      {discount && (
        <p className="text-sm text-green-600">Скидка: {discount}</p>
      )}
      {promo_labels && promo_labels.length > 0 && (
        <p className="text-xs text-gray-800">Промо: {promo_labels.join(', ')}</p>
      )}

      {/* Дата обновления */}
      {parsedDate && (
        <p className="mt-2 text-xs text-gray-500">Обновлено: {parsedDate}</p>
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
    category: PropTypes.string,
    marketplace: PropTypes.string,
    price_old: PropTypes.string,
    price_new: PropTypes.string,
    discount: PropTypes.string,
    promo_labels: PropTypes.arrayOf(PropTypes.string),
    parsed_at: PropTypes.string
  }).isRequired,
  filterCategory: PropTypes.string,
  filterMarketplace: PropTypes.string,
};

ProductCard.defaultProps = {
  filterCategory: null,
  filterMarketplace: null,
};

export default ProductCard;
