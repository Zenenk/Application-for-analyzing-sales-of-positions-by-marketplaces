import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
// Глобальные стили (TailwindCSS)
import './index.css';

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(
  // Рендерим приложение внутри корневого элемента
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
