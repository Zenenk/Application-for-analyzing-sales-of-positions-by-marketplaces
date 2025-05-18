# syntax=docker/dockerfile:1.4

###################################
# Стадия 1: builder
###################################
FROM python:3.10-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_RETRIES=10 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       pkg-config \
       python3-dev \
       libcairo2-dev \
       libpango1.0-dev \
       libjpeg-dev \
       libpng-dev \
       libfreetype6-dev \
       libgl1-mesa-glx \
       libglib2.0-0 \
       libsm6 \
       libxrender1 \
       libxext6 \
       tesseract-ocr \
       libtesseract-dev \
       libdbus-1-3 \
       libatk1.0-0 \
       libatk-bridge2.0-0 \
       libatspi2.0-0 \
       libxcomposite1 \
       libxdamage1 \
       libxrandr2 \
       libgbm1 \
       libxkbcommon0 \
       libasound2 \
       libcups2 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir playwright easyocr

RUN playwright install chromium

###################################
# Стадия 2: финальный лёгкий образ
###################################
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Устанавливаем все зависимости для Playwright
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       fonts-dejavu-core \
       curl \
       libcups2 \
    && rm -rf /var/lib/apt/lists/*

# Копируем библиотеки и браузеры из builder
COPY --from=builder /usr/lib /usr/lib
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /ms-playwright /ms-playwright

# Копируем код
COPY . /app/backend
ENV PYTHONPATH=/app/backend

EXPOSE 5000

CMD ["python", "-m", "backend.app"]
