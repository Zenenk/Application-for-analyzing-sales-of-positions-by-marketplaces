# Используем официальный образ Python 3.10
FROM python:3.10-slim

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Для Tesseract OCR:
    tesseract-ocr tesseract-ocr-rus \
    # Для Selenium (Chrome):
    chromium-driver chromium \
    # Прочие зависимости для OpenCV и браузера:
    libgl1 libglib2.0-0 libxrender1 libsm6 libxext6 \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы зависимостей и устанавливаем pip-зависимости
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект в контейнер
COPY . /app

# Указываем порт для Flask
EXPOSE 5000

# Запускаем приложение
CMD ["python", "-u", "backend/app.py"]
