from sqlalchemy import Column, String, DateTime, JSON, Text, Integer, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid

from ...database_base import Base

class VectorEmbedding(Base):
    """Entidad para almacenar embeddings de archivos vectorizados"""
    
    __tablename__ = "vector_embeddings"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    file_path = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # 'scr', 'ncl', 'inc', 'prg'
    content_hash = Column(String, nullable=False, index=True)  # Hash del contenido para detectar cambios
    embedding = Column(JSON, nullable=False)  # Lista de floats del embedding
    file_metadata = Column(JSON, nullable=True)  # Metadatos extraídos del archivo
    config_id = Column(String, nullable=False, index=True)  # ID de la configuración
    repo_type = Column(String, nullable=False)  # 'source', 'frontend', 'backend'
    repo_branch = Column(String, nullable=False, default='main')
    vectorization_batch_id = Column(String, nullable=True)  # ID del lote de vectorización
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow()
        if not self.updated_at:
            self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la entidad a diccionario"""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'content_hash': self.content_hash,
            'embedding': self.embedding,
            'file_metadata': self.file_metadata or {},
            'config_id': self.config_id,
            'repo_type': self.repo_type,
            'repo_branch': self.repo_branch,
            'vectorization_batch_id': self.vectorization_batch_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VectorEmbedding':
        """Crea una instancia desde un diccionario"""
        return cls(**data)
    
    def update_embedding(self, new_embedding: List[float], new_metadata: Dict[str, Any] = None):
        """Actualiza el embedding y metadatos"""
        self.embedding = new_embedding
        if new_metadata:
            self.file_metadata = new_metadata
        self.updated_at = datetime.utcnow()
    
    def is_content_changed(self, new_content_hash: str) -> bool:
        """Verifica si el contenido del archivo ha cambiado"""
        return self.content_hash != new_content_hash
