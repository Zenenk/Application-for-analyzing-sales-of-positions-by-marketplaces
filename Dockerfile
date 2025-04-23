
---

#### Dockerfile (корневой)
```Dockerfile
# Stage 1: Сборка frontend
FROM node:16-alpine as build-frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# Stage 2: Сборка backend
FROM python:3.9-slim

# Установка системных зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget unzip \
    tesseract-ocr tesseract-ocr-rus \
    chromium-browser libsm6 libxext6 libxrender1 && \
    rm -rf /var/lib/apt/lists/*

# Установка ChromeDriver
RUN wget -q https://chromedriver.storage.googleapis.com/110.0.5481.77/chromedriver_linux64.zip -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin && \
    rm /tmp/chromedriver.zip && \
    chmod +x /usr/local/bin/chromedriver

WORKDIR /app
COPY backend/ ./backend/
COPY --from=build-frontend /app/frontend/build ./backend/static
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
