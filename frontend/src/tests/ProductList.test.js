import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductsContext } from '../components/ProductsProvider';
import ProductList from '../pages/ProductList';

describe('ProductList page', () => {
  const products = [
    { id: 1, name: 'Alpha', category: 'Cat1', marketplace: 'M1', article: '111' },
    { id: 2, name: 'Beta', category: 'Cat2', marketplace: 'M2', article: '222' },
    { id: 3, name: 'Gamma', category: 'Cat1', marketplace: 'M2', article: '123' }
  ];

  function renderWithContext(ui, { value }) {
    return render(
      <ProductsContext.Provider value={value}>
        {ui}
      </ProductsContext.Provider>
    );
  }

  test('renders all products initially', () => {
    renderWithContext(<ProductList />, { value: { products, loading: false, error: null } });
    // Должны увидеть все названия товаров
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Beta')).toBeInTheDocument();
    expect(screen.getByText('Gamma')).toBeInTheDocument();
  });

  test('filters products by category', () => {
    renderWithContext(<ProductList />, { value: { products, loading: false, error: null } });
    // Выбираем категорию "Cat1" в селекторе фильтра
    fireEvent.change(screen.getByLabelText(/Категория/i), { target: { value: 'Cat1' } });
    // Теперь должны отображаться только товары категории Cat1
    expect(screen.getByText('Alpha')).toBeInTheDocument();
    expect(screen.getByText('Gamma')).toBeInTheDocument();
    // Товар Beta (Cat2) не должен отображаться
    expect(screen.queryByText('Beta')).toBeNull();
  });

  test('filters products by marketplace', () => {
    renderWithContext(<ProductList />, { value: { products, loading: false, error: null } });
    // Выбираем маркетплейс "M2"
    fireEvent.change(screen.getByLabelText(/Маркетплейс/i), { target: { value: 'M2' } });
    // Ожидаем, что отображаются только товары с marketplace M2
    expect(screen.getByText('Beta')).toBeInTheDocument();
    expect(screen.getByText('Gamma')).toBeInTheDocument();
    // Товар Alpha (M1) не отображается
    expect(screen.queryByText('Alpha')).toBeNull();
  });

  test('filters products by article search', () => {
    renderWithContext(<ProductList />, { value: { products, loading: false, error: null } });
    // Вводим часть артикула "12" для поиска
    fireEvent.change(screen.getByLabelText(/Артикул/i), { target: { value: '12' } });
    // Должен остаться только товар с артикулом, содержащим "12" (Gamma имеет '123')
    expect(screen.getByText('Gamma')).toBeInTheDocument();
    expect(screen.queryByText('Alpha')).toBeNull();
    expect(screen.queryByText('Beta')).toBeNull();
  });
});
