import React, { useContext } from 'react';
import { ProductsContext } from '../components/ProductsProvider';

function ReportsPage() {
  const { products, lastRunTime } = useContext(ProductsContext);

  // Определяем, есть ли данные для формирования отчётов
  const hasData = products && products.length > 0;
  // Форматируем время последнего запуска анализа для отображения
  const lastRunStr = lastRunTime ? new Date(lastRunTime).toLocaleString() : null;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Отчёты</h1>
      {/* Если еще не запускали анализ, показываем уведомление */}
      {!hasData ? (
        <p>Отчёты будут доступны после проведения анализа.</p>
      ) : (
        <div className="bg-white p-4 rounded shadow max-w-md">
          {lastRunStr && (
            <p className="mb-4">Последний анализ: <strong>{lastRunStr}</strong></p>
          )}
          {/* Ссылки на скачивание отчетов. Предполагается, что бэкенд отдаёт файлы по этим URL */}
          <a 
            href="/api/download/pdf" 
            className="block px-4 py-2 mb-2 bg-blue-600 text-white text-center rounded hover:bg-blue-700"
            target="_blank" 
            rel="noopener noreferrer"
            download
          >
            Скачать PDF отчёт
          </a>
          <a 
            href="/api/download/csv" 
            className="block px-4 py-2 bg-blue-600 text-white text-center rounded hover:bg-blue-700"
            target="_blank" 
            rel="noopener noreferrer"
            download
          >
            Скачать CSV отчёт
          </a>
        </div>
      )}
    </div>
  );
}

export default ReportsPage;
