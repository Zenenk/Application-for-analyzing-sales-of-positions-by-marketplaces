import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import Settings from './components/Settings';
import { getItems } from './services/api';

function App() {
  const [items, setItems] = useState([]);
  const [view, setView] = useState('dashboard');

  useEffect(() => {
    fetchItems();
  }, []);

  const fetchItems = async () => {
    try {
      const data = await getItems();
      setItems(data);
    } catch (err) {
      console.error(err);
    }
  };

  const renderView = () => {
    if (view === 'dashboard') {
      return <Dashboard items={items} refresh={fetchItems} />;
    } else if (view === 'settings') {
      return <Settings />;
    }
  };

  return (
    <div>
      <header>
        <h1>Мониторинг маркетплейсов</h1>
        <nav>
          <button onClick={() => setView('dashboard')}>Дашборд</button>
          <button onClick={() => setView('settings')}>Настройки</button>
        </nav>
      </header>
      <main>
        {renderView()}
      </main>
    </div>
  );
}

export default App;
