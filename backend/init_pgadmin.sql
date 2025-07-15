-- Inicialización de la base de datos para IRIA NSDK
-- Versión compatible con pgAdmin 4
-- IMPORTANTE: Ejecutar este script DESPUÉS de crear la base de datos manualmente

-- Crear extensiones necesarias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Tabla de configuraciones
CREATE TABLE IF NOT EXISTS configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de análisis
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de módulos
CREATE TABLE IF NOT EXISTS modules (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    module_type VARCHAR(100) NOT NULL,
    config_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de pantallas
CREATE TABLE IF NOT EXISTS screens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    screen_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_configurations_name ON configurations(name);
CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);
CREATE INDEX IF NOT EXISTS idx_modules_type ON modules(module_type);

-- Función para actualizar automáticamente updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers para actualizar updated_at automáticamente
CREATE TRIGGER update_configurations_updated_at BEFORE UPDATE ON configurations FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_analyses_updated_at BEFORE UPDATE ON analyses FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_modules_updated_at BEFORE UPDATE ON modules FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_screens_updated_at BEFORE UPDATE ON screens FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 