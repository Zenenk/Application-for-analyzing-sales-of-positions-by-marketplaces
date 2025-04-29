import axios from 'axios';

// Базовый URL API берётся из переменной окружения или используется "/api" по умолчанию
const API_BASE = process.env.REACT_APP_API_BASE || '/api';

// Создаём экземпляр axios с базовым URL, чтобы не указывать его каждый раз
const apiClient = axios.create({
  baseURL: API_BASE
});

// Функция для запроса списка продуктов (GET /products)
export const getProducts = () => {
  return apiClient.get('/products');
};

// Функция для запуска анализа (POST /start)
export const startAnalysis = (config) => {
  // Отправляем POST запрос с JSON-конфигурацией анализа
  return apiClient.post('/start', config);
};

