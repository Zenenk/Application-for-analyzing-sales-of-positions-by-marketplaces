# Этап сборки фронтенд-приложения
FROM node:16-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Этап для запуска с nginx
FROM nginx:1.21-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY --from=build /app/build /usr/share/nginx/html
# По умолчанию nginx слушает на порту 80
