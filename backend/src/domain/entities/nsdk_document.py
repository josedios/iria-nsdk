"""
Entidad para documentos NSDK
"""
from sqlalchemy import Column, String, Integer, BigInteger, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from ...database_base import Base


class NSDKDocument(Base):
    __tablename__ = 'nsdk_documents'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(BigInteger)
    status = Column(String(50), default='processing')
    total_chunks = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relación con chunks (comentada temporalmente para evitar problemas de importación)
    # chunks = relationship("NSDKDocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    def to_dict(self):
        """Convierte la entidad a diccionario"""
        return {
            'id': str(self.id),
            'name': self.name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'status': self.status,
            'total_chunks': self.total_chunks,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
