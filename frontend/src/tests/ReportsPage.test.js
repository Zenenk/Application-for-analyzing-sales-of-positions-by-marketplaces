import React from 'react';
import { render, screen } from '@testing-library/react';
import { ProductsContext } from '../components/ProductsProvider';
import ReportsPage from '../pages/ReportsPage';

describe('ReportsPage', () => {
  test('shows message when no data', () => {
    render(
      <ProductsContext.Provider value={{ products: [], lastRunTime: null }}>
        <ReportsPage />
      </ProductsContext.Provider>
    );
    expect(screen.getByText(/Отчёты будут доступны/)).toBeInTheDocument();
  });

  test('shows download links when data is available', () => {
    const fakeDate = new Date(2025, 0, 1, 12, 0, 0); // 1 Jan 2025 12:00:00
    render(
      <ProductsContext.Provider value={{ products: [{}], lastRunTime: fakeDate }}>
        <ReportsPage />
      </ProductsContext.Provider>
    );
    // Должно отображаться время последнего анализа и ссылки на скачивание
    expect(screen.getByText(/Последний анализ/)).toBeInTheDocument();
    expect(screen.getByText(/Скачать PDF отчёт/)).toBeInTheDocument();
    expect(screen.getByText(/Скачать CSV отчёт/)).toBeInTheDocument();
    // Проверяем, что ссылки имеют правильные href
    const pdfLink = screen.getByText(/PDF/).closest('a');
    const csvLink = screen.getByText(/CSV/).closest('a');
    expect(pdfLink).toHaveAttribute('href', '/api/download/pdf');
    expect(csvLink).toHaveAttribute('href', '/api/download/csv');
  });
});
