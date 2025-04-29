import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { ProductsContext } from '../components/ProductsProvider';
import ProductDetails from '../pages/ProductDetails';

describe('ProductDetails page', () => {
  const product = {
    id: 5,
    name: 'Test Product',
    category: 'CategoryX',
    marketplace: 'MarketY',
    article: 'XYZ123',
    currentSales: 100,
    previousSales: 80,
    image: 'https://via.placeholder.com/150',
    history: [
      { date: '2023-01-01', sales: 50 },
      { date: '2023-02-01', sales: 80 },
      { date: '2023-03-01', sales: 100 }
    ]
  };

  function renderWithRouterAndContext(productId, value) {
    render(
      <ProductsContext.Provider value={value}>
        <MemoryRouter initialEntries={[`/product/${productId}`]}>
          <Routes>
            <Route path="/product/:id" element={<ProductDetails />} />
          </Routes>
        </MemoryRouter>
      </ProductsContext.Provider>
    );
  }

  test('displays product details when product found', () => {
    renderWithRouterAndContext(5, { products: [product] });
    // Название товара
    expect(screen.getByText(/Test Product/)).toBeInTheDocument();
    // Категория, Маркетплейс, Артикул
    expect(screen.getByText(/CategoryX/)).toBeInTheDocument();
    expect(screen.getByText(/MarketY/)).toBeInTheDocument();
    expect(screen.getByText(/XYZ123/)).toBeInTheDocument();
    // Текущие и предыдущие продажи
    expect(screen.getByText(/Текущие продажи/)).toBeInTheDocument();
    expect(screen.getByText(/100/)).toBeInTheDocument();
    expect(screen.getByText(/Предыдущие продажи/)).toBeInTheDocument();
    expect(screen.getByText(/80/)).toBeInTheDocument();
    // Проверяем наличие текста об изменении продаж (должно быть +25%)
    expect(screen.getByText(/25.0%/)).toBeInTheDocument();
    // Проверяем, что график рендерится (например, оси или подсказки)
    expect(screen.getByText('Продажи')).toBeInTheDocument(); // легенда графика
  });

  test('displays "not found" message for invalid product', () => {
    // Передаём контекст без продуктов, запрашиваем несуществующий id
    renderWithRouterAndContext(999, { products: [] });
    expect(screen.getByText(/Товар не найден/)).toBeInTheDocument();
  });
});
