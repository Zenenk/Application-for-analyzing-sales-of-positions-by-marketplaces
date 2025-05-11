import axios from 'axios';

// Базовый URL можно настроить через .env (REACT_APP_API_BASE); по умолчанию – префикс /api на текущем хосте
axios.defaults.baseURL = process.env.REACT_APP_API_BASE || '/api';

// Объект с методами API
const API = {
  startProcess(settings) {
    return axios.post('/start', settings || {}).then(res => res.data);
  },
  getDashboardData() {
    return axios.get('/dashboard').then(res => res.data);
  },
  getReportsData() {
    return axios.get('/reports').then(res => res.data);
  },
  getProductList() {
    return axios.get('/products').then(res => res.data);
  },
  downloadPdf() {
    window.open('/download/pdf', '_blank');
  },
  downloadCsv() {
    window.open('/download/csv', '_blank');
  }
};

// Именованный экспорт для getProducts
export function getProducts() {
  return API.getProductList();
}

// По-старому экспортируем API как default
export default API;
