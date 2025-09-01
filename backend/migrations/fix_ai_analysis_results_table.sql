-- Arreglar tabla ai_analysis_results para que coincida con nsdk_file_analyses
-- Eliminar tabla existente si existe
DROP TABLE IF EXISTS ai_analysis_results CASCADE;

-- Recrear tabla con el tipo correcto para file_analysis_id
CREATE TABLE ai_analysis_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_analysis_id VARCHAR(255) NOT NULL,
    
    -- Metadatos del análisis
    analysis_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_version VARCHAR(20) DEFAULT '1.0',
    
    -- Resultado del análisis
    analysis_summary TEXT,
    file_type VARCHAR(50),  -- screen|form|report|utility
    complexity VARCHAR(20), -- low|medium|high
    estimated_hours VARCHAR(10),
    
    -- Análisis frontend (JSON)
    frontend_analysis TEXT, -- JSON
    
    -- Análisis backend (JSON)  
    backend_analysis TEXT,  -- JSON
    
    -- Notas y problemas potenciales (JSON)
    migration_notes TEXT,   -- JSON
    potential_issues TEXT,  -- JSON
    
    -- Respuesta completa de la IA (para debugging)
    raw_ai_response TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraint
    FOREIGN KEY (file_analysis_id) REFERENCES nsdk_file_analyses(id) ON DELETE CASCADE
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_ai_analysis_file_id ON ai_analysis_results(file_analysis_id);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_complexity ON ai_analysis_results(complexity);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_file_type ON ai_analysis_results(file_type);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_created_at ON ai_analysis_results(created_at);

-- Función para actualizar updated_at
CREATE OR REPLACE FUNCTION update_ai_analysis_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger para actualizar updated_at automáticamente
DROP TRIGGER IF EXISTS update_ai_analysis_updated_at ON ai_analysis_results;
CREATE TRIGGER update_ai_analysis_updated_at
    BEFORE UPDATE ON ai_analysis_results
    FOR EACH ROW
    EXECUTE FUNCTION update_ai_analysis_updated_at();
