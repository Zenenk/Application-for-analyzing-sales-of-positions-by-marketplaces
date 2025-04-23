import React from 'react';

function Dashboard({ items, refresh }) {
  return (
    <div>
      <h2>Список товаров</h2>
      <button onClick={refresh}>Обновить данные</button>
      <table>
        <thead>
          <tr>
            <th>Название</th>
            <th>Маркетплейс</th>
            <th>Цена</th>
            <th>Промо</th>
          </tr>
        </thead>
        <tbody>
          {items.map(item => (
            <tr key={item.id}>
              <td>{item.name}</td>
              <td>{item.marketplace}</td>
              <td>{item.price}</td>
              <td>{item.promotion ? 'Да' : 'Нет'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default Dashboard;
