# Etap 1: Budowanie paczki z React/Vite
FROM node:22-alpine AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Etap 2: Serwowanie przez Nginx
FROM nginx:stable-alpine
COPY --from=build-stage /app/dist /usr/share/nginx/html
# Dodajemy nasz plik konfiguracyjny (utworzysz go w kolejnym kroku)
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]