import React from 'react';
import { render, screen } from '@testing-library/react';
import { ProductsContext } from '../components/ProductsProvider';
import Dashboard from '../pages/Dashboard';

describe('Dashboard page', () => {
  test('displays loading state', () => {
    // Рендерим Dashboard с контекстом, где loading = true
    render(
      <ProductsContext.Provider value={{ products: [], loading: true, error: null }}>
        <Dashboard />
      </ProductsContext.Provider>
    );
    expect(screen.getByText(/Загрузка данных/i)).toBeInTheDocument();
  });

  test('displays error message', () => {
    const errorMessage = 'Network Error';
    render(
      <ProductsContext.Provider value={{ products: [], loading: false, error: new Error(errorMessage) }}>
        <Dashboard />
      </ProductsContext.Provider>
    );
    expect(screen.getByText(/Ошибка загрузки/i)).toHaveTextContent(errorMessage);
  });

  test('displays metrics and top products', () => {
    // Создаём тестовые данные продуктов
    const products = [
      { id: 1, name: 'Product A', category: 'Cat1', marketplace: 'M1', article: 'A1', currentSales: 100, previousSales: 50 },
      { id: 2, name: 'Product B', category: 'Cat2', marketplace: 'M2', article: 'B1', currentSales: 200, previousSales: 150 },
      { id: 3, name: 'Product C', category: 'Cat1', marketplace: 'M1', article: 'C1', currentSales: 50, previousSales: 50 }
    ];
    render(
      <ProductsContext.Provider value={{ products, loading: false, error: null }}>
        <Dashboard />
      </ProductsContext.Provider>
    );
    // Проверяем отображение метрик
    expect(screen.getByText('Всего товаров')).toBeInTheDocument();
    expect(screen.getByText('3')).toBeInTheDocument(); // totalProducts = 3
    expect(screen.getByText('Категорий')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // unique categories = 2
    expect(screen.getByText('Маркетплейсов')).toBeInTheDocument();
    expect(screen.getByText('2')).toBeInTheDocument(); // unique marketplaces = 2
    // Проверяем, что названия топ товаров присутствуют (Product B имеет наибольшие продажи, должен быть первым)
    expect(screen.getByText('Product B')).toBeInTheDocument();
    expect(screen.getByText('Product A')).toBeInTheDocument();
  });
});
