-- Script para crear la base de datos IRIA NSDK
-- Ejecutar este script como superusuario (postgres) antes de init.sql

-- Crear la base de datos
CREATE DATABASE iria_nsdk_db
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Crear un usuario específico para la aplicación (opcional)
CREATE USER iria_user WITH PASSWORD 'tu_password_seguro';

-- Dar permisos al usuario
GRANT ALL PRIVILEGES ON DATABASE iria_nsdk_db TO iria_user;

-- Conectar a la base de datos creada
\c iria_nsdk_db;

-- Dar permisos adicionales al usuario
GRANT ALL ON SCHEMA public TO iria_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO iria_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO iria_user; 