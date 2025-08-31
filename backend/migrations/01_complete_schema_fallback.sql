-- =====================================================
-- ESQUEMA COMPLETO DE BASE DE DATOS - IRIA NSDK (FALLBACK)
-- =====================================================
-- Versión alternativa que usa funciones UUID nativas de PostgreSQL
-- Útil cuando la extensión uuid-ossp no está disponible
-- Fecha: $(Get-Date -Format "yyyy-MM-dd")
-- Versión: 1.0.1

-- =====================================================
-- 1. VERIFICACIÓN DE EXTENSIÓN UUID
-- =====================================================
DO $$
BEGIN
    -- Intentar crear la extensión uuid-ossp
    BEGIN
        CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
        RAISE NOTICE '✅ Extensión uuid-ossp creada/verificada correctamente';
    EXCEPTION WHEN OTHERS THEN
        RAISE NOTICE '⚠️ No se pudo crear la extensión uuid-ossp: %', SQLERRM;
        RAISE NOTICE '📝 Continuando con funciones UUID nativas de PostgreSQL';
    END;
END $$;

-- =====================================================
-- 2. FUNCIÓN UUID FALLBACK
-- =====================================================
-- Crear función UUID personalizada si uuid_generate_v4 no está disponible
CREATE OR REPLACE FUNCTION generate_uuid()
RETURNS UUID AS $$
BEGIN
    -- Intentar usar uuid_generate_v4 si está disponible
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'uuid_generate_v4') THEN
        RETURN uuid_generate_v4();
    ELSE
        -- Fallback: usar función nativa de PostgreSQL
        RETURN gen_random_uuid();
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Verificar que tenemos una función UUID disponible
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname IN ('uuid_generate_v4', 'gen_random_uuid')) THEN
        RAISE NOTICE '✅ Función UUID disponible verificada';
    ELSE
        RAISE EXCEPTION '❌ No hay función UUID disponible. PostgreSQL debe ser versión 13+ para gen_random_uuid()';
    END IF;
END $$;

-- =====================================================
-- 3. TABLA DE CONFIGURACIONES
-- =====================================================
CREATE TABLE IF NOT EXISTS configurations (
    id UUID PRIMARY KEY DEFAULT generate_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    config_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 4. TABLA DE DIRECTORIOS NSDK
-- =====================================================
CREATE TABLE IF NOT EXISTS nsdk_directories (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    path VARCHAR(1000) NOT NULL,
    repository_name VARCHAR(255) NOT NULL,
    parent_id VARCHAR(255),
    level INTEGER DEFAULT 0,
    file_count INTEGER DEFAULT 0,
    dir_count INTEGER DEFAULT 0,
    total_size_kb INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Clave foránea para jerarquía de directorios
    CONSTRAINT fk_nsdk_directories_parent 
        FOREIGN KEY (parent_id) REFERENCES nsdk_directories(id) ON DELETE CASCADE
);

-- =====================================================
-- 5. TABLA DE ANÁLISIS DE ARCHIVOS NSDK
-- =====================================================
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

-- =====================================================
-- 6. TABLA DE LOGS DE SINCRONIZACIÓN
-- =====================================================
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

-- =====================================================
-- 7. TABLA DE METADATOS DE REPOSITORIOS
-- =====================================================
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

-- =====================================================
-- 8. TABLA DE ANÁLISIS (LEGACY - MANTENER COMPATIBILIDAD)
-- =====================================================
CREATE TABLE IF NOT EXISTS analyses (
    id UUID PRIMARY KEY DEFAULT generate_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    results JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 9. TABLA DE MÓDULOS (LEGACY - MANTENER COMPATIBILIDAD)
-- =====================================================
-- ELIMINADA: Esta funcionalidad la maneja nsdk_directories
-- Los módulos son directorios en el repositorio NSDK

-- =====================================================
-- 10. TABLA DE PANTALLAS (LEGACY - MANTENER COMPATIBILIDAD)
-- =====================================================
-- ELIMINADA: Esta funcionalidad la maneja nsdk_file_analyses
-- Las pantallas son archivos .SCR analizados individualmente

-- =====================================================
-- 11. ÍNDICES PARA OPTIMIZAR RENDIMIENTO
-- =====================================================

-- Índices para configurations
CREATE INDEX IF NOT EXISTS idx_configurations_name ON configurations(name);

-- Índices para nsdk_directories
CREATE INDEX IF NOT EXISTS idx_nsdk_directories_repository ON nsdk_directories(repository_name);
CREATE INDEX IF NOT EXISTS idx_nsdk_directories_parent ON nsdk_directories(parent_id);
CREATE INDEX IF NOT EXISTS idx_nsdk_directories_level ON nsdk_directories(level);
CREATE INDEX IF NOT EXISTS idx_nsdk_directories_path ON nsdk_directories(path);

-- Índices para nsdk_file_analyses
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_repository ON nsdk_file_analyses(repository_name);
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_file_type ON nsdk_file_analyses(file_type);
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_status ON nsdk_file_analyses(analysis_status);
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_file_path ON nsdk_file_analyses(file_path);
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_created_at ON nsdk_file_analyses(created_at);
CREATE INDEX IF NOT EXISTS idx_nsdk_file_analyses_repo_path ON nsdk_file_analyses(repository_name, file_path);

-- Índices para nsdk_sync_logs
CREATE INDEX IF NOT EXISTS idx_nsdk_sync_logs_repository ON nsdk_sync_logs(repository_name);
CREATE INDEX IF NOT EXISTS idx_nsdk_sync_logs_status ON nsdk_sync_logs(sync_status);
CREATE INDEX IF NOT EXISTS idx_nsdk_sync_logs_started_at ON nsdk_sync_logs(started_at);

-- Índices para nsdk_repository_metadata
CREATE INDEX IF NOT EXISTS idx_nsdk_repo_metadata_name ON nsdk_repository_metadata(repository_name);
CREATE INDEX IF NOT EXISTS idx_nsdk_repo_metadata_sync_status ON nsdk_repository_metadata(sync_status);

-- Índices para tablas legacy
CREATE INDEX IF NOT EXISTS idx_analyses_status ON analyses(status);
-- ELIMINADO: idx_modules_type (tabla modules eliminada)

-- =====================================================
-- 12. FUNCIÓN PARA ACTUALIZAR TIMESTAMPS
-- =====================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- =====================================================
-- 13. TRIGGERS PARA ACTUALIZAR TIMESTAMPS AUTOMÁTICAMENTE
-- =====================================================

-- Triggers para tablas principales
CREATE TRIGGER update_configurations_updated_at 
    BEFORE UPDATE ON configurations FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nsdk_directories_updated_at 
    BEFORE UPDATE ON nsdk_directories FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nsdk_file_analyses_updated_at 
    BEFORE UPDATE ON nsdk_file_analyses FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_nsdk_repository_metadata_updated_at 
    BEFORE UPDATE ON nsdk_repository_metadata FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Triggers para tablas legacy
CREATE TRIGGER update_analyses_updated_at 
    BEFORE UPDATE ON analyses FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ELIMINADOS: Triggers para modules y screens (tablas eliminadas)

-- =====================================================
-- 14. DATOS INICIALES
-- =====================================================

-- Insertar metadatos de repositorio por defecto
INSERT INTO nsdk_repository_metadata (repository_name, sync_status) 
VALUES ('nsdk-sources', 'unknown')
ON CONFLICT (repository_name) DO NOTHING;

-- =====================================================
-- 15. COMENTARIOS DE DOCUMENTACIÓN
-- =====================================================
COMMENT ON TABLE configurations IS 'Configuraciones del sistema IRIA NSDK';
COMMENT ON TABLE nsdk_directories IS 'Estructura jerárquica de directorios NSDK';
COMMENT ON TABLE nsdk_file_analyses IS 'Análisis detallado de archivos NSDK';
COMMENT ON TABLE nsdk_sync_logs IS 'Logs de sincronización de repositorios';
COMMENT ON TABLE nsdk_repository_metadata IS 'Metadatos y estado de repositorios';
COMMENT ON TABLE analyses IS 'Análisis generales del sistema (legacy)';
-- ELIMINADOS: Comentarios para modules y screens (tablas eliminadas)

-- =====================================================
-- 16. VERIFICACIÓN FINAL
-- =====================================================
-- Este comando verifica que todas las tablas se crearon correctamente
DO $$
DECLARE
    expected_tables TEXT[] := ARRAY[
        'configurations', 'nsdk_directories', 'nsdk_file_analyses', 
        'nsdk_sync_logs', 'nsdk_repository_metadata', 'analyses'
    ];
    current_table TEXT;
    table_exists BOOLEAN;
BEGIN
    FOREACH current_table IN ARRAY expected_tables
    LOOP
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = current_table
        ) INTO table_exists;
        
        IF table_exists THEN
            RAISE NOTICE '✅ Tabla % creada correctamente', current_table;
        ELSE
            RAISE NOTICE '❌ ERROR: Tabla % NO se creó', current_table;
        END IF;
    END LOOP;
    
    RAISE NOTICE '🎯 Esquema de base de datos completado. Revisar logs anteriores para verificar estado.';
    RAISE NOTICE '📝 Función UUID utilizada: %', 
        CASE 
            WHEN EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'uuid_generate_v4') THEN 'uuid_generate_v4 (extensión uuid-ossp)'
            WHEN EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'gen_random_uuid') THEN 'gen_random_uuid (nativa PostgreSQL)'
            ELSE 'generate_uuid (función personalizada)'
        END;
END $$;
