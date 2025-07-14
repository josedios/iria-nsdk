FROM node:18-alpine

# Establecer directorio de trabajo
WORKDIR /app

# Instalar Angular CLI globalmente
RUN npm install -g @angular/cli@17

# Copiar package.json y package-lock.json
COPY package*.json ./

# Instalar dependencias
RUN npm ci --only=production

# Copiar código fuente
COPY . .

# Exponer puerto
EXPOSE 4200

# Comando por defecto para desarrollo
CMD ["ng", "serve", "--host", "0.0.0.0", "--port", "4200"]

# Multi-stage build para producción
FROM node:18-alpine as build

WORKDIR /app

# Instalar Angular CLI
RUN npm install -g @angular/cli@17

# Copiar archivos de configuración
COPY package*.json ./
COPY angular.json ./
COPY tsconfig.json ./
COPY tsconfig.app.json ./

# Instalar dependencias
RUN npm ci

# Copiar código fuente
COPY src ./src

# Construir para producción
RUN ng build --configuration production

# Etapa de producción con Nginx
FROM nginx:alpine as production

# Copiar archivos construidos
COPY --from=build /app/dist/prompt-maestro-frontend /usr/share/nginx/html

# Copiar configuración de Nginx
COPY nginx.conf /etc/nginx/nginx.conf

# Exponer puerto 80
EXPOSE 80

# Comando por defecto
CMD ["nginx", "-g", "daemon off;"]