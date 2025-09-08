"""
Entidad para chunks de documentos NSDK
"""
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import json

from ...database_base import Base


class NSDKDocumentChunk(Base):
    __tablename__ = 'nsdk_document_chunks'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey('nsdk_documents.id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    chunk_title = Column(String(500))
    chunk_section = Column(String(500))
    chunk_type = Column(String(100), default='section')
    embedding = Column(ARRAY(Float))  # Array de floats para PostgreSQL
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relación con documento (comentada temporalmente para evitar problemas de importación)
    # document = relationship("NSDKDocument", back_populates="chunks")
    
    def to_dict(self):
        """Convierte la entidad a diccionario"""
        return {
            'id': str(self.id),
            'document_id': str(self.document_id),
            'chunk_index': self.chunk_index,
            'chunk_text': self.chunk_text,
            'chunk_title': self.chunk_title,
            'chunk_section': self.chunk_section,
            'chunk_type': self.chunk_type,
            'embedding': self.embedding,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
