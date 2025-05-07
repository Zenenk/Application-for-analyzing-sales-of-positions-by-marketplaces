import pytest
from backend.app import app

@pytest.fixture
def client(tmp_path, monkeypatch):
    """
    Тестовый клиент Flask, cwd — tmp_path, чтобы файлы создавались в изолированной директории.
    """
    # Все файловые операции (exported_*.csv/.pdf и scheduled_*.csv/.pdf) будут в tmp_path
    monkeypatch.chdir(tmp_path)
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client
