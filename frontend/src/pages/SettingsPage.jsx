// frontend/src/pages/SettingsPage.jsx
import React, { useState } from 'react';
import API from '../services/api';

const SettingsPage = () => {
  // Параметры парсинга
  const [marketplace, setMarketplace] = useState('Ozon');
  const [parseType, setParseType]     = useState('category');
  const [query, setQuery]             = useState('');
  const [limit, setLimit]             = useState(10);

  // Ответы и ошибки
  const [startMessage, setStartMessage] = useState(null);
  const [startError, setStartError]     = useState(null);

  // Параметры планирования
  const [scheduleInterval, setScheduleInterval] = useState(1);
  const [scheduleMessage, setScheduleMessage]   = useState(null);
  const [scheduleError, setScheduleError]       = useState(null);
  const [scheduling, setScheduling]             = useState(false);

  // Импорт CSV
  const [csvFile, setCsvFile]                   = useState(null);
  const [importingCsv, setImportingCsv]         = useState(false);
  const [csvMessage, setCsvMessage]             = useState(null);
  const [csvError, setCsvError]                 = useState(null);

  // Импорт скриншота
  const [screenshotFile, setScreenshotFile]             = useState(null);
  const [screenshotMarketplace, setScreenshotMarketplace] = useState('Ozon');
  const [importingScreenshot, setImportingScreenshot]     = useState(false);
  const [screenshotMessage, setScreenshotMessage]         = useState(null);
  const [screenshotError, setScreenshotError]             = useState(null);

  return (
    <div className="p-4 space-y-8">
      {/* Настройки парсинга */}
      <div className="space-y-4 border p-4 rounded">
        <h2 className="text-lg font-bold">Настройки парсинга</h2>

        {/* Marketplace */}
        <div>
          <label className="block">Маркетплейс</label>
          <select
            value={marketplace}
            onChange={e => setMarketplace(e.target.value)}
            className="border rounded px-2 py-1 w-full"
          >
            <option value="Ozon">Ozon</option>
            <option value="Wildberries">Wildberries</option>
          </select>
        </div>

        {/* Тип запроса */}
        <div>
          <label className="block">Тип запроса</label>
          <select
            value={parseType}
            onChange={e => setParseType(e.target.value)}
            className="border rounded px-2 py-1 w-full"
          >
            <option value="category">Категория</option>
            <option value="product">Товар</option>
          </select>
        </div>

        {/* Query */}
        <div>
          <label className="block">
            {parseType === 'category'
              ? 'Название категории'
              : 'Артикул товара'}
          </label>
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            className="border rounded px-2 py-1 w-full"
            placeholder="Например: хлебцы или 1234567"
          />
        </div>

        {/* Limit */}
        {parseType === 'category' && (
          <div>
            <label className="block">Кол-во товаров (до 50)</label>
            <input
              type="number"
              min="1"
              max="50"
              value={limit}
              onChange={e =>
                setLimit(
                  Math.min(50, Math.max(1, parseInt(e.target.value, 10)))
                )
              }
              className="border rounded px-2 py-1 w-full"
            />
          </div>
        )}

        {/* Интервал планирования */}
        <div>
          <label className="block">Интервал скрапинга (дней)</label>
          <input
            type="number"
            min="1"
            value={scheduleInterval}
            onChange={e => setScheduleInterval(Math.max(1, +e.target.value))}
            className="border rounded px-2 py-1 w-full"
          />
        </div>

        {/* Кнопка запуска анализа */}
        <button
          onClick={async () => {
            setStartMessage(null);
            setStartError(null);
            try {
              const settings = {
                marketplace,
                type: parseType,
                query,
                limit,
                scheduleInterval
              };
              const result = await API.startProcess(settings);
              setStartMessage(
                `Успешно: получено ${result.products?.length ?? 0} товаров.`
              );
            } catch (err) {
              setStartError(
                'Ошибка при запуске процесса: ' +
                (err.response?.data?.error || err.message)
              );
            }
          }}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Запустить анализ
        </button>
        {startMessage && <div className="text-green-600">{startMessage}</div>}
        {startError && <div className="text-red-600">{startError}</div>}
      </div>

      {/* Импорт CSV */}
      <div className="space-y-4 border p-4 rounded">
        <h2 className="text-lg font-bold">Импорт CSV</h2>
        <input
          type="file"
          accept=".csv"
          onChange={e => setCsvFile(e.target.files[0])}
          className="border px-2 py-1 rounded w-full"
        />
        <button
          onClick={async () => {
            setCsvMessage(null);
            setCsvError(null);
            setImportingCsv(true);
            try {
              const result = await API.importCsv(csvFile);
              setCsvMessage(
                `Импортировано: ${result.inserted}. Ошибок: ${
                  result.errors.length
                }`
              );
            } catch (err) {
              setCsvError(
                'Ошибка при импорте: ' +
                (err.response?.data?.error || err.message)
              );
            } finally {
              setImportingCsv(false);
            }
          }}
          disabled={importingCsv}
          className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
        >
          {importingCsv ? 'Импортируем...' : 'Загрузить CSV'}
        </button>
        {csvMessage && <div className="text-green-600">{csvMessage}</div>}
        {csvError && <div className="text-red-600">{csvError}</div>}
      </div>

      {/* Импорт скриншота */}
      <div className="space-y-4 border p-4 rounded">
        <h2 className="text-lg font-bold">Импорт из скриншота</h2>
        <div>
          <label className="block">Маркетплейс</label>
          <select
            value={screenshotMarketplace}
            onChange={e => setScreenshotMarketplace(e.target.value)}
            className="border rounded px-2 py-1 w-full"
          >
            <option value="Ozon">Ozon</option>
            <option value="Wildberries">Wildberries</option>
          </select>
        </div>
        <input
          type="file"
          accept="image/png, image/jpeg"
          onChange={e => setScreenshotFile(e.target.files[0])}
          className="border px-2 py-1 rounded w-full"
        />
        <button
          onClick={async () => {
            setScreenshotMessage(null);
            setScreenshotError(null);
            setImportingScreenshot(true);
            try {
              await API.importScreenshot(
                screenshotFile,
                screenshotMarketplace
              );
              setScreenshotMessage('Скриншот успешно импортирован.');
            } catch (err) {
              setScreenshotError(
                'Ошибка импорта скриншота: ' +
                (err.response?.data?.error || err.message)
              );
            } finally {
              setImportingScreenshot(false);
            }
          }}
          disabled={importingScreenshot}
          className="bg-purple-500 text-white px-4 py-2 rounded hover:bg-purple-600"
        >
          {importingScreenshot ? 'Импортируем...' : 'Загрузить скриншот'}
        </button>
        {screenshotMessage && <div className="text-green-600">{screenshotMessage}</div>}
        {screenshotError && <div className="text-red-600">{screenshotError}</div>}
      </div>
    </div>
  );
};

export default SettingsPage;
