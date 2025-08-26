from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import Column, String, Integer, DateTime, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

@dataclass
class NSDKFileAnalysis:
    """Entidad para almacenar el análisis de archivos NSDK"""
    file_path: str
    file_name: str
    file_type: str  # 'module', 'screen', 'include', 'program'
    repository_name: str
    line_count: int
    char_count: int
    size_kb: float
    function_count: int
    functions: List[str]
    field_count: int
    fields: List[str]
    button_count: int
    buttons: List[str]
    module_name: Optional[str] = None
    screen_name: Optional[str] = None
    analysis_status: str = 'pending'  # 'pending', 'analyzing', 'analyzed', 'error'
    analysis_date: Optional[datetime] = None
    file_metadata: Optional[Dict[str, Any]] = None
    id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class NSDKFileAnalysisModel(Base):
    """Modelo SQLAlchemy para NSDKFileAnalysis"""
    __tablename__ = 'nsdk_file_analyses'
    
    id = Column(String, primary_key=True)
    file_path = Column(String, nullable=False, index=True)
    file_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False, index=True)
    repository_name = Column(String, nullable=False, index=True)
    line_count = Column(Integer, nullable=False)
    char_count = Column(Integer, nullable=False)
    size_kb = Column(Integer, nullable=False)
    function_count = Column(Integer, default=0)
    functions = Column(JSON, default=list)
    field_count = Column(Integer, default=0)
    fields = Column(JSON, default=list)
    button_count = Column(Integer, default=0)
    buttons = Column(JSON, default=list)
    module_name = Column(String)
    screen_name = Column(String)
    analysis_status = Column(String, default='pending', index=True)
    analysis_date = Column(DateTime(timezone=True))
    file_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el modelo a diccionario"""
        return {
            'id': self.id,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'repository_name': self.repository_name,
            'line_count': self.line_count,
            'char_count': self.char_count,
            'size_kb': self.size_kb,
            'function_count': self.function_count,
            'functions': self.functions or [],
            'field_count': self.field_count,
            'fields': self.fields or [],
            'button_count': self.button_count,
            'buttons': self.buttons or [],
            'module_name': self.module_name,
            'screen_name': self.screen_name,
            'analysis_status': self.analysis_status,
            'analysis_date': self.analysis_date.isoformat() if self.analysis_date else None,
            'file_metadata': self.file_metadata or {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
