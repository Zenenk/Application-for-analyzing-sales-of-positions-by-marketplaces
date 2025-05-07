import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { ProductsContext } from '../components/ProductsProvider';
import * as api from '../services/api';
import SettingsPage from '../pages/SettingsPage';

describe('SettingsPage', () => {
  // Подготавливаем mock для функции startAnalysis
  beforeEach(() => {
    jest.spyOn(api, 'startAnalysis').mockResolvedValue({ data: {} });
  });
  afterEach(() => {
    jest.restoreAllMocks();
  });

  test('renders form fields and triggers analysis start', async () => {
    const refreshMock = jest.fn();
    const setLastRunTimeMock = jest.fn();
    render(
      <ProductsContext.Provider value={{ refresh: refreshMock, setLastRunTime: setLastRunTimeMock }}>
        <SettingsPage />
      </ProductsContext.Provider>
    );
    // Проверяем наличие основных элементов формы
    expect(screen.getByText(/Маркетплейсы для анализа/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Категории/)).toBeInTheDocument();
    expect(screen.getByLabelText(/Включить изображения/)).toBeInTheDocument();
    // Отмечаем первый маркетплейс и вводим категорию
    const firstMpCheckbox = screen.getByLabelText('Ozon');
    fireEvent.click(firstMpCheckbox);
    fireEvent.change(screen.getByLabelText(/Категории/), { target: { value: 'TestCat' } });
    // Снимаем галочку "Включить изображения"
    fireEvent.click(screen.getByLabelText(/Включить изображения/));
    // Нажимаем кнопку "Начать анализ"
    const startButton = screen.getByText('Начать анализ');
    fireEvent.click(startButton);
    // Кнопка должна стать disabled и изменить текст на "Запуск..."
    expect(startButton).toHaveAttribute('disabled');
    expect(startButton).toHaveTextContent('Запуск...');
    // Дождёмся вызова API и обновления
    await waitFor(() => expect(api.startAnalysis).toHaveBeenCalled());
    // Проверяем, что API вызван с ожидаемым конфигом
    expect(api.startAnalysis).toHaveBeenCalledWith({
      marketplaces: ['Ozon'],
      categories: ['TestCat'],
      includeImages: false
    });
    // После успешного вызова должны быть вызваны refresh и setLastRunTime
    await waitFor(() => {
      expect(refreshMock).toHaveBeenCalled();
      expect(setLastRunTimeMock).toHaveBeenCalled();
    });
  });
});
