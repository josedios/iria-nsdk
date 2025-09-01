-- Migración para tablas de documentos NSDK
-- 003_create_nsdk_documents_tables.sql

-- Tabla para documentos NSDK
CREATE TABLE IF NOT EXISTS nsdk_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size BIGINT,
    status VARCHAR(50) DEFAULT 'processing',
    total_chunks INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para chunks de documentos
CREATE TABLE IF NOT EXISTS nsdk_document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES nsdk_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_title VARCHAR(500),
    chunk_section VARCHAR(500),
    chunk_type VARCHAR(100) DEFAULT 'section',
    embedding VECTOR(1536), -- Para PostgreSQL con pgvector
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Índices para optimizar búsquedas
CREATE INDEX IF NOT EXISTS idx_nsdk_documents_name ON nsdk_documents(name);
CREATE INDEX IF NOT EXISTS idx_nsdk_documents_status ON nsdk_documents(status);
CREATE INDEX IF NOT EXISTS idx_nsdk_chunks_document_id ON nsdk_document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_nsdk_chunks_embedding ON nsdk_document_chunks USING ivfflat (embedding vector_cosine_ops);

-- Comentarios
COMMENT ON TABLE nsdk_documents IS 'Documentos técnicos NSDK procesados';
COMMENT ON TABLE nsdk_document_chunks IS 'Chunks de documentos NSDK con embeddings';
COMMENT ON COLUMN nsdk_document_chunks.embedding IS 'Embedding vector para búsqueda semántica';
