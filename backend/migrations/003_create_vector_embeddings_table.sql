-- Migración para crear la tabla de embeddings vectorizados
-- Fecha: 2024-01-XX
-- Descripción: Tabla para almacenar embeddings de archivos vectorizados para evitar recálculo

CREATE TABLE IF NOT EXISTS vector_embeddings (
    id VARCHAR(36) PRIMARY KEY,
    file_path VARCHAR(500) NOT NULL,
    file_name VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    content_hash VARCHAR(32) NOT NULL,
    embedding JSONB NOT NULL,
    file_metadata JSONB,
    config_id VARCHAR(36) NOT NULL,
    repo_type VARCHAR(50) NOT NULL,
    repo_branch VARCHAR(100) NOT NULL DEFAULT 'main',
    vectorization_batch_id VARCHAR(36),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT idx_file_path_config UNIQUE (file_path, config_id)
);

-- Crear índices para optimizar búsquedas
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_content_hash ON vector_embeddings (content_hash);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_config_id ON vector_embeddings (config_id);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_config_repo_branch ON vector_embeddings (config_id, repo_type, repo_branch);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_file_type ON vector_embeddings (file_type);
CREATE INDEX IF NOT EXISTS idx_vector_embeddings_created_at ON vector_embeddings (created_at);

-- Función para actualizar automáticamente updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at automáticamente
DROP TRIGGER IF EXISTS update_vector_embeddings_updated_at ON vector_embeddings;
CREATE TRIGGER update_vector_embeddings_updated_at 
    BEFORE UPDATE ON vector_embeddings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Comentarios sobre la tabla
COMMENT ON TABLE vector_embeddings IS 'Almacena embeddings vectorizados de archivos para evitar recálculo';
COMMENT ON COLUMN vector_embeddings.id IS 'ID único del embedding';
COMMENT ON COLUMN vector_embeddings.file_path IS 'Ruta completa del archivo';
COMMENT ON COLUMN vector_embeddings.file_name IS 'Nombre del archivo';
COMMENT ON COLUMN vector_embeddings.file_type IS 'Tipo de archivo (scr, ncl, inc, prg)';
COMMENT ON COLUMN vector_embeddings.content_hash IS 'Hash MD5 del contenido para detectar cambios';
COMMENT ON COLUMN vector_embeddings.embedding IS 'Vector de embedding (JSONB array de floats)';
COMMENT ON COLUMN vector_embeddings.file_metadata IS 'Metadatos extraídos del archivo';
COMMENT ON COLUMN vector_embeddings.config_id IS 'ID de la configuración';
COMMENT ON COLUMN vector_embeddings.repo_type IS 'Tipo de repositorio (source, frontend, backend)';
COMMENT ON COLUMN vector_embeddings.repo_branch IS 'Rama del repositorio';
COMMENT ON COLUMN vector_embeddings.vectorization_batch_id IS 'ID del lote de vectorización';
COMMENT ON COLUMN vector_embeddings.created_at IS 'Fecha de creación';
COMMENT ON COLUMN vector_embeddings.updated_at IS 'Fecha de última actualización';
