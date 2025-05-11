# syntax=docker/dockerfile:1.4
###################################
# 1. Собираем зависимости
###################################
FROM python:3.10-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_RETRIES=10 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Системные библиотеки и python3-opencv
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-rus \
      chromium \
      libpq-dev \
      libgl1 libglib2.0-0 libxrender1 libsm6 libxext6 \
      python3-opencv \
 && rm -rf /var/lib/apt/lists/*

# Копируем зависимости
COPY requirements.txt .

# Кэшируем скачанные wheel между сборками
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir playwright playwright-stealth easyocr

# Устанавливаем браузер Chromium для Playwright
RUN playwright install chromium

###################################
# 2. Финальный образ
###################################
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Берём системные библиотеки и пакеты из builder
COPY --from=builder /usr/lib /usr/lib
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /ms-playwright /ms-playwright

COPY . /app/backend

ENV PYTHONPATH=/app/backend

EXPOSE 5000

CMD ["python", "-m", "backend.app"]
