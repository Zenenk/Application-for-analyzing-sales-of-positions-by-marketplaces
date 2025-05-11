# --- Стадия сборки фронтенда ---
FROM node:18-alpine AS build

# Рабочая директория
WORKDIR /app

# Копируем только манифесты и настройки npm
COPY package.json package-lock.json ./
# Копируем правила npm (таймауты и отключение строгой проверки потоков)
COPY .npmrc ./

# Устанавливаем зависимости (взятие из .npmrc)
RUN npm install

# Копируем весь код (исключая node_modules благодаря .dockerignore)
COPY . .

# Собираем в production
RUN npm run build

# --- Стадия отдачи через nginx ---
FROM nginx:1.21-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
