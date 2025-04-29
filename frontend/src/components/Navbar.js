import React from 'react';
import { NavLink } from 'react-router-dom';

// Навигационное меню для переключения между страницами приложения
function Navbar() {
  return (
    <nav className="bg-gray-800 text-white px-4 py-3 flex space-x-4">
      {/* Ссылки NavLink позволяют переходить по маршрутам. 
           Класс active добавляется к активной ссылке автоматически. */}
      <NavLink 
        to="/" 
        className={({ isActive }) => isActive ? 'underline text-blue-200' : 'text-white'} 
      >
        Обзор
      </NavLink>
      <NavLink 
        to="/products" 
        className={({ isActive }) => isActive ? 'underline text-blue-200' : 'text-white'}
      >
        Товары
      </NavLink>
      <NavLink 
        to="/settings" 
        className={({ isActive }) => isActive ? 'underline text-blue-200' : 'text-white'}
      >
        Настройки
      </NavLink>
      <NavLink 
        to="/reports" 
        className={({ isActive }) => isActive ? 'underline text-blue-200' : 'text-white'}
      >
        Отчёты
      </NavLink>
    </nav>
  );
}

export default Navbar;
