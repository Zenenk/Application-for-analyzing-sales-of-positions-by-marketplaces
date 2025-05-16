import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import ProductsProvider from './components/ProductsProvider';
import Dashboard from './pages/Dashboard';
import ProductList from './pages/ProductList';
import ProductDetails from './pages/ProductDetails';
import SettingsPage from './pages/SettingsPage';
import ReportsPage from './pages/ReportsPage';

function App() {
  return (
    <ProductsProvider>
      <BrowserRouter>
        <Navbar />
        <div className="p-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/products" element={<ProductList />} />
            <Route path="/product/:id" element={<ProductDetails />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
          </Routes>
        </div>
      </BrowserRouter>
    </ProductsProvider>
  );
}

export default App;
