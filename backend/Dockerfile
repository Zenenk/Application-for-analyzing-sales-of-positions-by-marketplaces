# syntax=docker/dockerfile:1.4
FROM python:3.10-slim AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_RETRIES=10 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Системные библиотеки для сборки C-расширений (pycairo, Pillow и т.п.)
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
    && rm -rf /var/lib/apt/lists/*

# Копируем и устанавливаем Python-зависимости
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir playwright easyocr

# Устанавливаем браузер Chromium для Playwright
RUN playwright install chromium

###################################
# Финальный лёгкий образ
###################################
FROM python:3.10-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Копируем интерпретаторные и системные библиотеки из builder
COPY --from=builder /usr/lib /usr/lib
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /ms-playwright /ms-playwright

# Копируем сам код бэкенда
COPY . /app/backend

ENV PYTHONPATH=/app/backend

EXPOSE 5000

CMD ["python", "-m", "backend.app"]
