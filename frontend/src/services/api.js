// api.js – helper for making authenticated requests to backend API
const API_URL = process.env.REACT_APP_API_URL || "";  // например, "" если backend на том же домене
const TOKEN = process.env.REACT_APP_API_TOKEN || "";

async function request(path, options = {}) {
  // Добавляем токен авторизации ко всем запросам
  const headers = options.headers || {};
  headers["Authorization"] = `Bearer ${TOKEN}`;
  headers["Content-Type"] = "application/json";
  const opts = { ...options, headers };
  const response = await fetch(API_URL + path, opts);
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  // Если есть ответ с JSON – парсим, иначе возвращаем as is (например, файл)
  const contentType = response.headers.get("Content-Type") || "";
  if (contentType.includes("application/json")) {
    return await response.json();
  }
  return response;
}

// Функции для конкретных действий API:
export async function getProducts() {
  return request("/api/products", { method: "GET" });
}
export async function addProduct(url) {
  return request("/api/products", { method: "POST", body: JSON.stringify({ url }) });
}
export async function deleteProduct(id) {
  return request(`/api/products/${id}`, { method: "DELETE" });
}
export async function getProductHistory(id) {
  return request(`/api/products/${id}/history`, { method: "GET" });
}
export async function exportData(format = "csv") {
  // Для экспорта получаем ответ и предлагаем скачать файл
  const res = await request(`/api/export?format=${format}`, { method: "GET" });
  // Создаем blob и скачиваем (поскольку fetch не скачивает автоматически)
  const blob = await res.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `export_results.${format}`;
  document.body.appendChild(a);
  a.click();
  a.remove();
}
