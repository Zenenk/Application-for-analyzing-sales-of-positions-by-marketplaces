# syntax=docker/dockerfile:1.4

###################################
# СТАДИЯ 1: builder
###################################
FROM python:3.10-slim AS builder

ENV \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_RETRIES=10 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# 1) Системные зависимости
RUN --mount=type=cache,target=/var/cache/apt/archives \
    apt-get update && \
    apt-get install -y \
      ca-certificates \
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
      libxext6 && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Устанавливаем только CPU-версии PyTorch
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
      torch==2.0.0+cpu \
      torchvision==0.15.1+cpu \
      --index-url https://download.pytorch.org/whl/cpu

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install \
      scipy scikit-image python-bidi PyYAML shapely

# Устанавливаем EasyOCR без подтягивания своих deps
RUN pip install easyocr --no-deps

# Playwright
RUN pip install playwright && playwright install-deps && playwright install chromium

###################################
# СТАДИЯ 2: runtime
###################################
FROM python:3.10-slim

ENV \
    DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

# Только runtime-зависимости
RUN apt-get update && \
    apt-get install -y \
      ca-certificates \
      fonts-dejavu-core \
      curl \
      libcups2 \
      libnss3 \
      libnspr4 \
      libatk1.0-0 \
      libatk-bridge2.0-0 \
      libatspi2.0-0 \
      libxcomposite1 \
      libxdamage1 \
      libxrandr2 \
      libgbm1 \
      libxkbcommon0 \
      libasound2 && \
    rm -rf /var/lib/apt/lists/*

# Копируем всё из builder
COPY --from=builder /usr/lib            /usr/lib
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /ms-playwright      /ms-playwright

# Копируем код
COPY . /app/backend
ENV PYTHONPATH=/app/backend

EXPOSE 5000
CMD ["python", "-m", "backend.app"]
