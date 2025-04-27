import React, { useEffect, useState } from "react";
import { getProducts, addProduct, deleteProduct, exportData } from "./api";
import ProductList from "./components/ProductList";
import ProductForm from "./components/ProductForm";
import "./App.css";

function App() {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Загрузка списка товаров при монтировании
  useEffect(() => {
    async function fetchData() {
      try {
        const items = await getProducts();
        setProducts(items);
      } catch (err) {
        console.error("Failed to fetch products:", err);
        setError("Ошибка загрузки списка товаров");
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);

  const handleAddProduct = async (url) => {
    setError("");
    try {
      const newProduct = await addProduct(url);
      setProducts([...products, newProduct]);
    } catch (err) {
      console.error("Add product failed:", err);
      setError("Не удалось добавить товар. Проверьте URL.");
    }
  };

  const handleDeleteProduct = async (id) => {
    setError("");
    try {
      await deleteProduct(id);
      setProducts(products.filter(p => p.id !== id));
    } catch (err) {
      console.error("Delete failed:", err);
      setError("Не удалось удалить товар.");
    }
  };

  const handleExport = async (format) => {
    setError("");
    try {
      await exportData(format);
      // Возможно, сообщить пользователю, что скачивание началось
    } catch (err) {
      console.error("Export failed:", err);
      setError("Экспорт не удался.");
    }
  };

  return (
    <div className="App">
      <h1>Анализ продаж на маркетплейсах</h1>
      {error && <div className="error">{error}</div>}
      {/* Форма добавления нового товара */}
      <ProductForm onAdd={handleAddProduct} />
      {/* Кнопки экспорта */}
      <div className="export-buttons">
        <button onClick={() => handleExport("csv")}>💾 Экспорт CSV</button>
        <button onClick={() => handleExport("pdf")}>📄 Экспорт PDF</button>
      </div>
      {/* Список товаров */}
      {loading ? (
        <p>Загрузка...</p>
      ) : (
        <ProductList products={products} onDelete={handleDeleteProduct} />
      )}
    </div>
  );
}

export default App;
