import axios from 'axios';

// Базовый URL для всех запросов (подставляется при сборке из .env)
axios.defaults.baseURL = process.env.REACT_APP_API_BASE || '/api';

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
    window.open(`${axios.defaults.baseURL}/download/pdf`, '_blank');
  },
  downloadCsv() {
    window.open(`${axios.defaults.baseURL}/download/csv`, '_blank');
  }
};

export function getProducts() {
  return API.getProductList();
}

API.importCsv = function(file) {
  const form = new FormData();
  form.append("file", file);
  return axios
    .post("/import/csv", form, {
      headers: { "Content-Type": "multipart/form-data" }
    })
    .then(res => res.data);
};

/**
 * Импорт данных из скриншота категории или товара.
 * @param {File} imageFile — PNG/JPG файла скриншота.
 * @param {string} marketplace — 'Ozon' или 'Wildberries'.
 */
export const importScreenshot = async (imageFile, marketplace) => {
    const fd = new FormData();
    fd.append("image", imageFile);
    fd.append("marketplace", marketplace);
    const res = await axios.post("/api/import/screenshot", fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return res.data;
};

/**
 * Получить историю изменений по артикулу.
 * @param {string} article
 * @returns {Promise<Array<{parsed_at:string, price:string, price_old:string, price_new:string, discount:string, quantity:string}>>}
 */
export const getProductHistory = async (article) => {
  const res = await axios.get(`/api/products/history/${encodeURIComponent(article)}`);
  return res.data;
};

export default API;
