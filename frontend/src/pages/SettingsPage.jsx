// frontend/src/pages/SettingsPage.jsx

import React, { useState } from 'react';
import API from '../services/api';

function SettingsPage() {
  const [csvFile, setCsvFile]     = useState(null);
  const [message, setMessage]     = useState(null);
  const [importing, setImporting] = useState(false);

  const handleFileChange = (e) => {
    setCsvFile(e.target.files[0]);
    setMessage(null);
  };

  const handleImport = async () => {
    if (!csvFile) {
      setMessage({ type: 'error', text: 'Выберите CSV-файл' });
      return;
    }
    setImporting(true);
    try {
      const result = await API.importCsv(csvFile);
      setMessage({ type: 'success', text: `Импортировано: ${result.inserted}. Ошибок: ${result.errors.length}` });
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.error || 'Ошибка при загрузке';
      setMessage({ type: 'error', text: msg });
    } finally {
      setImporting(false);
    }
  };

  return (
    <div className="settings-page space-y-4">
      {/* Существующая кнопка запуска процесса */}
      <button
        onClick={() => API.startProcess()}
        className="px-4 py-2 bg-blue-600 text-white rounded"
      >
        Start
      </button>

      <hr />

      {/* Новая секция для импорта CSV */}
      <h2 className="text-xl font-semibold">Импорт CSV</h2>
      <input
        type="file"
        accept=".csv"
        onChange={handleFileChange}
        className="block"
      />
      <button
        onClick={handleImport}
        disabled={importing}
        className={`px-4 py-2 rounded ${importing ? 'bg-gray-400' : 'bg-green-600 text-white'}`}
      >
        {importing ? 'Импортируем...' : 'Загрузить CSV'}
      </button>

      {message && (
        <div className={`mt-2 ${message.type==='error' ? 'text-red-600' : 'text-green-600'}`}>
          {message.text}
        </div>
      )}
    </div>
  );
}

export default SettingsPage;
