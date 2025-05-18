# syntax=docker/dockerfile:1.4

# ───── СТАДИЯ 1: сборка React ─────
FROM node:18-alpine AS build
WORKDIR /app
COPY package.json package-lock.json .npmrc ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --prefer-offline --no-audit --progress=false
COPY . ./
RUN npm run build

# ───── СТАДИЯ 2: финальный образ на nginx ─────
FROM nginx:1.21-alpine

# Установим bash и netcat
RUN apk add --no-cache bash netcat-openbsd

# Копируем и делаем исполняемым скрипт ожидания
COPY wait-for-it.sh /wait-for-it.sh
RUN chmod +x /wait-for-it.sh

# Очищаем дефолтный HTML и копируем ваш билд
RUN rm -rf /usr/share/nginx/html/*
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

# Ждём бэкенд (host="backend", port="5000"), потом сразу nginx
ENTRYPOINT ["/wait-for-it.sh", "backend", "5000", "--", "nginx", "-g", "daemon off;"]
