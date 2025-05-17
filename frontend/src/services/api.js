// frontend/src/services/api.js
import axios from 'axios';

// Базовый URL для всех запросов: '/api' или переопределяемый через env
axios.defaults.baseURL = process.env.REACT_APP_API_BASE || '/api';

const API = {
  // Запуск процесса парсинга с JSON-конфигом
  startProcess: async (settings) => {
    const res = await axios.post('/start', settings);
    return res.data;
  },

  // Импорт CSV-файла
  importCsv: async (file) => {
    const fd = new FormData();
    fd.append('file', file);
    const res = await axios.post('/import/csv', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  // Импорт из скриншота
  importScreenshot: async (imageFile, marketplace) => {
    const fd = new FormData();
    fd.append('image', imageFile);
    fd.append('marketplace', marketplace);
    const res = await axios.post('/import/screenshot', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return res.data;
  },

  // Получить список продуктов
  getProductList: async () => {
    const res = await axios.get('/products');
    return res.data;
  },

  // Получить историю по артикулу
  getProductHistory: async (article) => {
    const res = await axios.get(
      `/products/history/${encodeURIComponent(article)}`
    );
    return res.data;
  },

  // Общие метрики дашборда
  getDashboard: async () => {
    const res = await axios.get('/dashboard');
    return res.data;
  },

  // Список доступных отчётов
  getReports: async () => {
    const res = await axios.get('/reports');
    return res.data;
  },

  // URL для скачивания отчёта 'csv' или 'pdf'
  downloadReportUrl: (kind) => {
    return `${axios.defaults.baseURL}/download/${kind}`;
  },

  // URL для экспорта PDF по товару
  exportProductUrl: (article) => {
    return `${axios.defaults.baseURL}/export/product/${encodeURIComponent(
      article
    )}`;
  },

  // Изменить расписание
  setSchedule: async (intervalDays) => {
    const res = await axios.post('/schedule', { interval: intervalDays });
    return res.data;
  },

};

export default API;

