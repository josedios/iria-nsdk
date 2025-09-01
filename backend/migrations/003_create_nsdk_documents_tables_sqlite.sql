-- Migración para tablas de documentos NSDK (SQLite compatible)
-- 003_create_nsdk_documents_tables_sqlite.sql

-- Tabla para documentos NSDK
CREATE TABLE IF NOT EXISTS nsdk_documents (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_size INTEGER,
    status TEXT DEFAULT 'processing',
    total_chunks INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabla para chunks de documentos
CREATE TABLE IF NOT EXISTS nsdk_document_chunks (
    id TEXT PRIMARY KEY DEFAULT (lower(hex(randomblob(4))) || '-' || lower(hex(randomblob(2))) || '-4' || substr(lower(hex(randomblob(2))),2) || '-' || substr('89ab',abs(random()) % 4 + 1, 1) || substr(lower(hex(randomblob(2))),2) || '-' || lower(hex(randomblob(6)))),
    document_id TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    chunk_title TEXT,
    chunk_section TEXT,
    chunk_type TEXT DEFAULT 'section',
    embedding TEXT, -- JSON string para SQLite
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES nsdk_documents(id) ON DELETE CASCADE
);

-- Índices para optimizar búsquedas
CREATE INDEX IF NOT EXISTS idx_nsdk_documents_name ON nsdk_documents(name);
CREATE INDEX IF NOT EXISTS idx_nsdk_documents_status ON nsdk_documents(status);
CREATE INDEX IF NOT EXISTS idx_nsdk_chunks_document_id ON nsdk_document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_nsdk_chunks_chunk_index ON nsdk_document_chunks(document_id, chunk_index);
