import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import ProductsProvider from './components/ProductsProvider';
import Dashboard from './pages/Dashboard';
import ProductList from './pages/ProductList';
import ProductDetails from './pages/ProductDetails';
import SettingsPage from './pages/SettingsPage';
import ReportsPage from './pages/ReportsPage';

// Корневой компонент приложения. Здесь подключаются контекст продуктов, маршрутизатор и навигация.
function App() {
  return (
    // Провайдер контекста продуктов предоставляет данные всем вложенным компонентам
    <ProductsProvider>
      <BrowserRouter>
        {/* Навигационная панель, отображается на всех страницах */}
        <Navbar />
        <div className="p-4"> {/* Основной контейнер со отступами */}
          <Routes>
            {/* Определение маршрутов для страниц интерфейса */}
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<ProductList />} />
            <Route path="/product/:id" element={<ProductDetails />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            {/* В SwaggerUI (опционально) можно добавить маршрут /docs, если необходимо */}
          </Routes>
        </div>
      </BrowserRouter>
    </ProductsProvider>
  );
}

export default App;
