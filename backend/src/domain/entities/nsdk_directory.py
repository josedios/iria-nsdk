from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

@dataclass
class NSDKDirectory:
    """Entidad para almacenar la estructura de directorios NSDK"""
    name: str
    path: str
    repository_name: str
    parent_id: Optional[str] = None
    level: int = 0
    file_count: int = 0
    dir_count: int = 0
    total_size_kb: float = 0.0
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class NSDKDirectoryModel(Base):
    """Modelo SQLAlchemy para NSDKDirectory"""
    __tablename__ = 'nsdk_directories'
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    path = Column(String, nullable=False, index=True)
    repository_name = Column(String, nullable=False, index=True)
    parent_id = Column(String, ForeignKey('nsdk_directories.id'), nullable=True, index=True)
    level = Column(Integer, default=0, index=True)
    file_count = Column(Integer, default=0)
    dir_count = Column(Integer, default=0)
    total_size_kb = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    parent = relationship("NSDKDirectoryModel", remote_side=[id], backref="children")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'name': self.name,
            'path': self.path,
            'repository_name': self.repository_name,
            'parent_id': self.parent_id,
            'level': self.level,
            'file_count': self.file_count,
            'dir_count': self.dir_count,
            'total_size_kb': self.total_size_kb,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
