import React, { useState } from 'react';
import API from '../services/api';

function SettingsPage() {
  // Пример состояния настроек (если есть поля настроек, инициализируйте их здесь)
  const [settings, setSettings] = useState({/* начальные настройки */});

  // Обработчик нажатия на кнопку "Start"
  const handleStart = async () => {
    try {
      // Отправляем настройки на бекенд через API; ожидаем успешного запуска
      await API.startProcess(settings);
      // Дополнительно: можно отобразить уведомление о успехе или перенаправить на другую страницу
      console.log('Process started successfully');
    } catch (error) {
      console.error('Failed to start process:', error);
      // Здесь можно установить сообщение об ошибке в состоянии, чтобы отобразить в UI
    }
  };

  return (
    <div className="settings-page">
      {/* Поля настройки (если необходимы) */}
      {/* <input ... onChange={...setSettings({...})} /> */}
      <button onClick={handleStart}>Start</button>
    </div>
  );
}

export default SettingsPage;
