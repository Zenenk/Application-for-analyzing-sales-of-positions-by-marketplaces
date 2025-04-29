import React, { useState, useContext } from 'react';
import { ProductsContext } from '../components/ProductsProvider';
import { startAnalysis } from '../services/api';

function SettingsPage() {
  // Локальное состояние для параметров конфигурации анализа
  const [selectedMarketplaces, setSelectedMarketplaces] = useState([]);  // выбраны ли маркетплейсы
  const [categoriesInput, setCategoriesInput] = useState('');            // ввод категорий через запятую
  const [includeImages, setIncludeImages] = useState(true);              // флаг "включить изображения"
  const [starting, setStarting] = useState(false);                       // состояние запуска анализа

  // Доступ к функции обновления продуктов и отметке времени последнего запуска из контекста
  const { refresh, setLastRunTime } = useContext(ProductsContext);

  // Варианты доступных маркетплейсов
  const marketplacesOptions = ['Ozon', 'Wildberries', 'Яндекс Маркет'];

  // Обработчики изменения параметров
  const toggleMarketplace = (mp) => {
    // Добавляем или убираем маркетплейс из выбранных
    setSelectedMarketplaces(prev => 
      prev.includes(mp) ? prev.filter(x => x !== mp) : [...prev, mp]
    );
  };
  const handleCategoriesChange = (e) => setCategoriesInput(e.target.value);
  const handleIncludeImagesChange = (e) => setIncludeImages(e.target.checked);

  // Обработчик отправки конфигурации и запуска анализа
  const handleStartAnalysis = async (e) => {
    e.preventDefault();
    if (starting) return;
    setStarting(true);
    try {
      // Формируем конфигурацию для запроса /start
      const config = {
        marketplaces: selectedMarketplaces,
        categories: categoriesInput 
          ? categoriesInput.split(',').map(s => s.trim()).filter(s => s) 
          : [],  // разбиваем строку категорий на массив
        includeImages: includeImages
      };
      // Отправляем POST запрос на запуск анализа
      await startAnalysis(config);
      // Успешно запущено: обновляем время последнего запуска и перечитываем продукты из базы
      setLastRunTime(new Date());
      refresh();
      alert('Анализ запущен успешно!');
    } catch (err) {
      console.error('Ошибка запуска анализа:', err);
      alert('Не удалось запустить анализ. Проверьте настройки и подключение к серверу.');
    } finally {
      setStarting(false);
    }
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Настройки анализа</h1>
      <form onSubmit={handleStartAnalysis} className="bg-white p-4 rounded shadow max-w-lg">
        {/* Чекбоксы для выбора маркетплейсов */}
        <fieldset className="mb-4">
          <legend className="text-sm font-medium text-gray-700 mb-2">Маркетплейсы для анализа:</legend>
          {marketplacesOptions.map(mp => (
            <label key={mp} className="block text-gray-800">
              <input 
                type="checkbox" 
                value={mp}
                checked={selectedMarketplaces.includes(mp)}
                onChange={() => toggleMarketplace(mp)}
                className="mr-2"
              />
              {mp}
            </label>
          ))}
        </fieldset>
        {/* Поле для ввода категорий */}
        <div className="mb-4">
          <label htmlFor="categories" className="block text-sm font-medium text-gray-700">
            Категории (через запятую, пусто = все)
          </label>
          <input 
            id="categories" 
            type="text" 
            value={categoriesInput} 
            onChange={handleCategoriesChange}
            placeholder="Пример: Электроника, Одежда" 
            className="mt-1 block w-full border-gray-300 rounded"
          />
        </div>
        {/* Чекбокс включения изображений */}
        <div className="mb-6">
          <label className="inline-flex items-center text-gray-800">
            <input 
              type="checkbox" 
              checked={includeImages} 
              onChange={handleIncludeImagesChange} 
              className="mr-2"
            />
            Включить изображения товаров
          </label>
        </div>
        {/* Кнопка запуска анализа */}
        <button 
          type="submit" 
          className={`px-4 py-2 text-white rounded ${starting ? 'bg-gray-400 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-700'}`}
          disabled={starting}
        >
          {starting ? 'Запуск...' : 'Начать анализ'}
        </button>
      </form>
    </div>
  );
}

export default SettingsPage;
