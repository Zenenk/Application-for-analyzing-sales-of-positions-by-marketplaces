import React, { useEffect, useState } from 'react';
import API from '../services/api';

function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Получаем данные для дашборда при монтировании компонента
    API.getDashboard()
      .then((dashboardData) => {
        setData(dashboardData);
      })
      .catch((err) => {
        console.error('Error fetching dashboard data:', err);
        setError('Не удалось загрузить данные дашборда');
      });
  }, []);

  if (error) {
    return <div className="dashboard-error">{error}</div>;
  }

  if (!data) {
    return <div className="dashboard-loading">Загрузка...</div>;
  }

  return (
    <div className="dashboard">
      <h1>Dashboard</h1>
      {/* Предполагается, что data содержит нужную информацию для отображения */}
      {/* Пример отображения данных: */}
      {typeof data === 'object' ? (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      ) : (
        <div>{String(data)}</div>
      )}
    </div>
  );
}

export default Dashboard;
