from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid
from uuid import UUID

class VectorizationBatchStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class VectorizationBatchType(Enum):
    REPOSITORY = "repository"      # Vectorización completa de un repo
    MODULE = "module"              # Vectorización de un módulo específico
    FILES = "files"                # Vectorización de archivos específicos
    INCREMENTAL = "incremental"    # Vectorización incremental

@dataclass
class VectorizationBatch:
    name: str
    batch_type: VectorizationBatchType
    config_id: UUID                    # ID de la configuración
    repo_type: str                     # Tipo de repositorio: 'source', 'frontend', 'backend'
    source_repo_branch: str
    id: Optional[str] = None
    status: VectorizationBatchStatus = VectorizationBatchStatus.PENDING
    total_files: int = 0
    processed_files: int = 0
    successful_files: int = 0
    failed_files: int = 0
    file_ids: List[str] = None
    error_files: List[str] = None
    metadata: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.file_ids is None:
            self.file_ids = []
        if self.error_files is None:
            self.error_files = []
        if self.metadata is None:
            self.metadata = {}
    
    def start_processing(self):
        """Inicia el procesamiento del lote"""
        self.status = VectorizationBatchStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def complete_processing(self):
        """Marca el lote como completado"""
        self.status = VectorizationBatchStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def fail_processing(self, error_message: str):
        """Marca el lote como fallido"""
        self.status = VectorizationBatchStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if 'error_message' not in self.metadata:
            self.metadata['error_message'] = error_message
    
    def add_file(self, file_id: str):
        """Añade un archivo al lote"""
        if file_id not in self.file_ids:
            self.file_ids.append(file_id)
            self.total_files += 1
            self.updated_at = datetime.utcnow()
    
    def mark_file_processed(self, file_id: str, success: bool = True):
        """Marca un archivo como procesado"""
        self.processed_files += 1
        if success:
            self.successful_files += 1
        else:
            self.failed_files += 1
            if file_id not in self.error_files:
                self.error_files.append(file_id)
        self.updated_at = datetime.utcnow()
    
    def get_progress_percentage(self) -> float:
        """Calcula el porcentaje de progreso"""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100
    
    def get_success_rate(self) -> float:
        """Calcula la tasa de éxito"""
        if self.processed_files == 0:
            return 0.0
        return (self.successful_files / self.processed_files) * 100
    
    def is_completed(self) -> bool:
        """Verifica si el lote está completado"""
        return self.status in [VectorizationBatchStatus.COMPLETED, VectorizationBatchStatus.FAILED]
    
    def get_duration(self) -> Optional[float]:
        """Obtiene la duración del procesamiento en segundos"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen del estado del lote"""
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status.value,
            'progress': self.get_progress_percentage(),
            'success_rate': self.get_success_rate(),
            'total_files': self.total_files,
            'processed_files': self.processed_files,
            'successful_files': self.successful_files,
            'failed_files': self.failed_files,
            'duration': self.get_duration()
        }
