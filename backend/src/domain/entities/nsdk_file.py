from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class NSDKFileType(Enum):
    SCR = "scr"           # Pantallas
    NCL = "ncl"           # Módulos
    INC = "inc"           # Includes
    PRG = "prg"           # Programas
    UNKNOWN = "unknown"

class NSDKFileStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    VECTORIZED = "vectorized"
    ERROR = "error"

@dataclass
class NSDKFile:
    name: str
    file_path: str
    file_type: NSDKFileType
    id: Optional[str] = None
    module_id: Optional[str] = None
    content: Optional[str] = None
    content_hash: Optional[str] = None
    vector_embedding: Optional[list] = None
    metadata: Optional[Dict[str, Any]] = None
    status: NSDKFileStatus = NSDKFileStatus.PENDING
    error_message: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.metadata is None:
            self.metadata = {}
    
    def update_status(self, new_status: NSDKFileStatus, error_message: Optional[str] = None):
        self.status = new_status
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def set_content(self, content: str):
        self.content = content
        self.content_hash = self._calculate_hash(content)
        self.updated_at = datetime.utcnow()
    
    def set_vector_embedding(self, embedding: list):
        self.vector_embedding = embedding
        self.status = NSDKFileStatus.VECTORIZED
        self.updated_at = datetime.utcnow()
    
    def _calculate_hash(self, content: str) -> str:
        """Calcula un hash simple del contenido para detectar cambios"""
        import hashlib
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get_display_name(self) -> str:
        """Obtiene el nombre para mostrar en la UI"""
        return self.name.replace('.SCR', '').replace('.NCL', '').replace('_', ' ').title()
    
    def is_vectorized(self) -> bool:
        """Verifica si el archivo está vectorizado"""
        return self.status == NSDKFileStatus.VECTORIZED and self.vector_embedding is not None
    
    def get_file_extension(self) -> str:
        """Obtiene la extensión del archivo"""
        return self.name.split('.')[-1].upper() if '.' in self.name else ''
    
    def get_relative_path(self) -> str:
        """Obtiene la ruta relativa del archivo"""
        return self.file_path.replace('\\', '/').split('/')[-2:] if '/' in self.file_path else [self.file_path]
