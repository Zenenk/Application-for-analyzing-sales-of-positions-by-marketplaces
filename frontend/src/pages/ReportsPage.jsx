import React, { useEffect, useState } from 'react';
import API from '../services/api';

function ReportsPage() {
  const [reports, setReports] = useState(null);
  const [error, setError]     = useState(null);

  useEffect(() => {
    API.getReports()
      .then(setReports)
      .catch(err => {
        console.error('Error fetching reports data:', err);
        setError('Не удалось загрузить отчёты');
      });
  }, []);

  if (error)    return <div className="text-red-600">{error}</div>;
  if (!reports) return <div>Загрузка отчётов...</div>;

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Отчёты</h1>
      <ul className="list-disc pl-5 mb-4">
        {reports.map(r => (
          <li key={r.id}>{r.title || r.name}</li>
        ))}
      </ul>
      <div className="space-x-2">
        <button
          onClick={() => API.exportPdf()}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Скачать PDF
        </button>
        <button
          onClick={() => API.exportCsv()}
          className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
        >
          Скачать CSV
        </button>
      </div>
    </div>
  );
}

export default ReportsPage;
