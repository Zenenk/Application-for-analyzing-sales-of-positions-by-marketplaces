import React, { useEffect, useState } from 'react';
import API from '../services/api';

function ReportsPage() {
  const [reports, setReports] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Получаем данные отчётов при монтировании
    API.getReportsData()
      .then((reportsData) => {
        setReports(reportsData);
      })
      .catch((err) => {
        console.error('Error fetching reports data:', err);
        setError('Не удалось загрузить отчёты');
      });
  }, []);

  if (error) {
    return <div className="reports-error">{error}</div>;
  }

  if (!reports) {
    return <div className="reports-loading">Загрузка отчётов...</div>;
  }

  return (
    <div className="reports-page">
      <h1>Reports</h1>
      {/* Отображаем список отчётов, если reports это массив */}
      {Array.isArray(reports) ? (
        <ul>
          {reports.map((report, index) => (
            <li key={report.id || index}>
              {report.title || report.name || `Report ${index + 1}`}
            </li>
          ))}
        </ul>
      ) : (
        // Если reports не массив (например, объект с данными отчётов)
        <pre>{JSON.stringify(reports, null, 2)}</pre>
      )}
      {/* Кнопки для скачивания отчётов в разных форматах */}
      <div className="report-downloads">
        <button onClick={API.downloadPdf}>Скачать PDF</button>
        <button onClick={API.downloadCsv}>Скачать CSV</button>
      </div>
    </div>
  );
}

export default ReportsPage;
