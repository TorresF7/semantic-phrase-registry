# --- Etapa 1: construcción con Vite ----------------------------------------
FROM node:24-alpine AS construccion

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

# Las variables VITE_* se incrustan en el paquete público en tiempo de
# construcción: nunca un secreto aquí.
ARG VITE_API_URL=/api/v1
ARG VITE_MAX_PHRASE_LENGTH=280
ARG VITE_API_TIMEOUT_MS=15000
ENV VITE_API_URL=$VITE_API_URL \
    VITE_MAX_PHRASE_LENGTH=$VITE_MAX_PHRASE_LENGTH \
    VITE_API_TIMEOUT_MS=$VITE_API_TIMEOUT_MS

RUN npm run build

# --- Etapa 2: nginx sin privilegios ----------------------------------------
# La variante unprivileged corre como usuario `nginx` y escucha en 8080.
FROM nginxinc/nginx-unprivileged:1.29-alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=construccion /app/dist /usr/share/nginx/html

EXPOSE 8080
