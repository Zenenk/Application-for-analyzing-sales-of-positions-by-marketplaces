# frontend/Dockerfile
# syntax=docker/dockerfile:1.4

FROM node:18-alpine AS build

WORKDIR /app

# 1) Скопировать package-файлы для кэширования зависимостей
COPY package.json package-lock.json .npmrc ./

# 2) Настройка npm для устойчивости к сбоям и установка зависимостей
RUN --mount=type=cache,target=/root/.npm \
    npm config set fetch-retries 5 && \
    npm config set fetch-retry-factor 2 && \
    npm config set fetch-retry-mintimeout 20000 && \
    npm config set fetch-retry-maxtimeout 60000 && \
    npm config set registry https://registry.npmjs.org/ && \
    npm ci --prefer-offline --no-audit --progress=false

# 3) Скопировать весь исходный код и собрать
COPY . ./
RUN npm run build

# Далее — nginx для раздачи
FROM nginx:1.21-alpine
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
