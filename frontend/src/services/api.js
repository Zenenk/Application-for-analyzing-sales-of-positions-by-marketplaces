// frontend/src/services/api.js
// Базовый URL для всех запросов: '/api' или переопределяемый через env
import axios from 'axios';

const host = window.location.hostname;       // "80.237.33.113"
const protocol = window.location.protocol;   // "http:"
const API_PORT = process.env.REACT_APP_API_PORT || '5001';

axios.defaults.baseURL = `${protocol}//${host}:${API_PORT}`;

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


  // Получить список продуктов
  getProductList: async () => {
    console.log('➡️ GET', axios.defaults.baseURL + '/products');
    const res = await axios.get('/products');
    console.log('⬅️', res.status, res.data);
    return res.data;
  },

  getProductHistory: async (article) => {
    const url = `/products/history/${encodeURIComponent(article)}`;
    console.log('➡️ GET', axios.defaults.baseURL + url);
    try {
      const res = await axios.get(url);
      console.log('⬅️', res.status, res.data);
      return res.data;
    } catch (err) {
      console.error('❌ HISTORY ERROR', err.response?.status, err.response?.data);
      throw err;
    }
  },

  // Список доступных отчётов
  getReports: async () => {
    const res = await axios.get('/reports');
    return res.data;
  },



  // Скачать из БД сразу новый CSV
  exportCsv: () => {
    window.open(`${axios.defaults.baseURL}/export/csv`, '_blank');
  },

  // Скачать из БД сразу новый PDF
  exportPdf: () => {
    window.open(`${axios.defaults.baseURL}/export/pdf`, '_blank');
  },


  // Общие метрики дашборда
  getDashboard: async () => {
    const res = await axios.get('/dashboard');
    return res.data;
  },

  
  // Список уникальных категорий из БД
  getCategories: async () => {
    const res = await axios.get('/categories');
    return res.data;
  },
  

  // Список уникальных маркетплейсов из БД
  getMarketplaces: async () => {
    const res = await axios.get('/marketplaces');
    return res.data;
  },

  // URL для скачивания отчёта 'csv' или 'pdf'
  downloadReportUrl: (kind) => {
    return `${axios.defaults.baseURL}/download/${kind}`;
  },

  // URL для экспорта PDF по товару
  exportProductUrl: (article) => {
    return `${axios.defaults.baseURL}/export/product/${encodeURIComponent(article)}`;
  },

  // Изменить расписание
  setSchedule: async (intervalDays) => {
    const res = await axios.post('/schedule', { interval: intervalDays });
    return res.data;
  },

};

export default API;

