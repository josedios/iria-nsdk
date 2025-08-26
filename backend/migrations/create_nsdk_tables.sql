-- Script de migración para crear tablas de análisis NSDK
-- Ejecutar este script en la base de datos PostgreSQL

-- Crear tabla para análisis de archivos NSDK
CREATE TABLE IF NOT EXISTS nsdk_file_analyses (
    id VARCHAR(255) PRIMARY KEY,
    file_path VARCHAR(1000) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    repository_name VARCHAR(255) NOT NULL,
    line_count INTEGER NOT NULL,
    char_count INTEGER NOT NULL,
    size_kb INTEGER NOT NULL,
    function_count INTEGER DEFAULT 0,
    functions JSONB DEFAULT '[]'::jsonb,
    field_count INTEGER DEFAULT 0,
    fields JSONB DEFAULT '[]'::jsonb,
    button_count INTEGER DEFAULT 0,
    buttons JSONB DEFAULT '[]'::jsonb,
    module_name VARCHAR(255),
    screen_name VARCHAR(255),
    analysis_status VARCHAR(50) DEFAULT 'pending',
    analysis_date TIMESTAMP WITH TIME ZONE,
    file_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_repository ON nsdk_file_analyses(repository_name);
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_file_type ON nsdk_file_analyses(file_type);
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_status ON nsdk_file_analyses(analysis_status);
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_file_path ON nsdk_file_analyses(file_path);
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_created_at ON nsdk_file_analyses(created_at);

-- Crear índice compuesto para búsquedas por repositorio y ruta
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_repo_path ON nsdk_file_analyses(repository_name, file_path);

-- Crear tabla para seguimiento de sincronización
CREATE TABLE IF NOT EXISTS nsdk_sync_logs (
    id SERIAL PRIMARY KEY,
    repository_name VARCHAR(255) NOT NULL,
    sync_type VARCHAR(50) NOT NULL, -- 'initial', 'incremental', 'cleanup'
    sync_status VARCHAR(50) NOT NULL, -- 'started', 'completed', 'failed'
    files_processed INTEGER DEFAULT 0,
    files_created INTEGER DEFAULT 0,
    files_updated INTEGER DEFAULT 0,
    files_skipped INTEGER DEFAULT 0,
    files_errors INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER
);

-- Crear índices para la tabla de logs
CREATE INDEX IF NOT EXISTS idx_nsdk_sync_logs_repository ON nsdk_sync_logs(repository_name);
CREATE INDEX IF NOT EXISTS idx_nsdk_sync_logs_status ON nsdk_sync_logs(sync_status);
CREATE INDEX IF NOT EXISTS idx_nsdk_sync_logs_started_at ON nsdk_sync_logs(started_at);

-- Crear tabla para metadatos de repositorios
CREATE TABLE IF NOT EXISTS nsdk_repository_metadata (
    id SERIAL PRIMARY KEY,
    repository_name VARCHAR(255) UNIQUE NOT NULL,
    last_sync_at TIMESTAMP WITH TIME ZONE,
    last_analysis_at TIMESTAMP WITH TIME ZONE,
    total_files INTEGER DEFAULT 0,
    analyzed_files INTEGER DEFAULT 0,
    pending_files INTEGER DEFAULT 0,
    error_files INTEGER DEFAULT 0,
    sync_status VARCHAR(50) DEFAULT 'unknown',
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Crear índices para metadatos de repositorios
CREATE INDEX IF NOT EXISTS idx_nsdk_repo_metadata_name ON nsdk_repository_metadata(repository_name);
CREATE INDEX IF NOT EXISTS idx_nsdk_repo_metadata_sync_status ON nsdk_repository_metadata(sync_status);

-- Insertar datos iniciales si es necesario
INSERT INTO nsdk_repository_metadata (repository_name, sync_status) 
VALUES ('nsdk-sources', 'unknown')
ON CONFLICT (repository_name) DO NOTHING;

-- Comentarios sobre las tablas
COMMENT ON TABLE nsdk_file_analyses IS 'Almacena el análisis de archivos NSDK extraídos de repositorios';
COMMENT ON TABLE nsdk_sync_logs IS 'Registra el historial de sincronizaciones de análisis NSDK';
COMMENT ON TABLE nsdk_repository_metadata IS 'Metadatos y estado de sincronización de repositorios NSDK';

-- Función para actualizar automáticamente updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Crear triggers para actualizar automáticamente updated_at
CREATE TRIGGER update_nsdk_file_analyses_updated_at 
    BEFORE UPDATE ON nsdk_file_analyses 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nsdk_repository_metadata_updated_at 
    BEFORE UPDATE ON nsdk_repository_metadata 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
