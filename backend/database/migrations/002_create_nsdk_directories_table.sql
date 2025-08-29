-- Crear tabla para directorios NSDK
CREATE TABLE IF NOT EXISTS nsdk_directories (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(500) NOT NULL,
    path TEXT NOT NULL,
    repository_name VARCHAR(255) NOT NULL,
    parent_id VARCHAR(255),
    level INTEGER DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    dir_count INTEGER DEFAULT 0,
    total_size_kb INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_id) REFERENCES nsdk_directories(id) ON DELETE CASCADE
);

-- Crear índices para mejorar el rendimiento
CREATE INDEX IF NOT EXISTS idx_nsdk_directories_repository_name ON nsdk_directories(repository_name);
CREATE INDEX IF NOT EXISTS idx_nsdk_directories_parent_id ON nsdk_directories(parent_id);
CREATE INDEX IF NOT EXISTS idx_nsdk_directories_level ON nsdk_directories(level);
CREATE INDEX IF NOT EXISTS idx_nsdk_directories_path ON nsdk_directories(path);

-- Crear índice compuesto para consultas frecuentes
CREATE INDEX IF NOT EXISTS idx_nsdk_directories_repo_parent ON nsdk_directories(repository_name, parent_id);

-- Comentarios sobre la estructura
COMMENT ON TABLE nsdk_directories IS 'Tabla para almacenar la estructura jerárquica de directorios NSDK';
COMMENT ON COLUMN nsdk_directories.id IS 'ID único del directorio';
COMMENT ON COLUMN nsdk_directories.name IS 'Nombre del directorio';
COMMENT ON COLUMN nsdk_directories.path IS 'Ruta completa del directorio en el sistema de archivos';
COMMENT ON COLUMN nsdk_directories.repository_name IS 'Nombre del repositorio al que pertenece';
COMMENT ON COLUMN nsdk_directories.parent_id IS 'ID del directorio padre (NULL para directorios raíz)';
COMMENT ON COLUMN nsdk_directories.level IS 'Nivel de profundidad en el árbol (0 = raíz)';
COMMENT ON COLUMN nsdk_directories.file_count IS 'Número de archivos en este directorio';
COMMENT ON COLUMN nsdk_directories.dir_count IS 'Número de subdirectorios en este directorio';
COMMENT ON COLUMN nsdk_directories.total_size_kb IS 'Tamaño total en KB de todos los archivos en este directorio';
