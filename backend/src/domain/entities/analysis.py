from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum
from datetime import datetime
import uuid

class AnalysisStatus(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class FrontendAnalysis:
    """Análisis de la parte frontend de una pantalla"""
    fields: List[Dict[str, Any]]
    validations: List[Dict[str, Any]]
    dependencies: List[str]
    buttons: List[Dict[str, Any]]
    presentation_logic: str
    ui_components: List[Dict[str, Any]]
    
    def __post_init__(self):
        if self.fields is None:
            self.fields = []
        if self.validations is None:
            self.validations = []
        if self.dependencies is None:
            self.dependencies = []
        if self.buttons is None:
            self.buttons = []
        if self.ui_components is None:
            self.ui_components = []

@dataclass
class BackendAnalysis:
    """Análisis de la parte backend de una pantalla"""
    business_logic: str
    sql_queries: List[Dict[str, Any]]
    validations: List[Dict[str, Any]]
    external_calls: List[Dict[str, Any]]
    data_transformations: List[Dict[str, Any]]
    dependencies: List[str]
    
    def __post_init__(self):
        if self.sql_queries is None:
            self.sql_queries = []
        if self.validations is None:
            self.validations = []
        if self.external_calls is None:
            self.external_calls = []
        if self.data_transformations is None:
            self.data_transformations = []
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class APIAnalysis:
    """Análisis de la API necesaria para una pantalla"""
    endpoints: List[Dict[str, Any]]
    openapi_spec: str
    security_requirements: List[Dict[str, Any]]
    data_models: List[Dict[str, Any]]
    error_handling: List[Dict[str, Any]]
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = []
        if self.security_requirements is None:
            self.security_requirements = []
        if self.data_models is None:
            self.data_models = []
        if self.error_handling is None:
            self.error_handling = []

@dataclass
class Analysis:
    id: str
    screen_id: str
    status: AnalysisStatus
    frontend_analysis: Optional[FrontendAnalysis] = None
    backend_analysis: Optional[BackendAnalysis] = None
    api_analysis: Optional[APIAnalysis] = None
    complexity_score: float = 0.0
    estimated_hours: float = 0.0
    migration_notes: str = ""
    error_message: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def update_status(self, new_status: AnalysisStatus):
        """Actualiza el estado del análisis"""
        self.status = new_status
        self.updated_at = datetime.utcnow()
        
        if new_status == AnalysisStatus.COMPLETED:
            self.completed_at = datetime.utcnow()
    
    def set_error(self, error_message: str):
        """Establece un error en el análisis"""
        self.status = AnalysisStatus.ERROR
        self.error_message = error_message
        self.updated_at = datetime.utcnow()
    
    def calculate_complexity(self) -> float:
        """Calcula la complejidad basada en el análisis"""
        complexity = 0.0
        
        if self.frontend_analysis:
            complexity += len(self.frontend_analysis.fields) * 0.5
            complexity += len(self.frontend_analysis.validations) * 1.0
            complexity += len(self.frontend_analysis.dependencies) * 1.5
            complexity += len(self.frontend_analysis.buttons) * 0.3
        
        if self.backend_analysis:
            complexity += len(self.backend_analysis.sql_queries) * 2.0
            complexity += len(self.backend_analysis.validations) * 1.5
            complexity += len(self.backend_analysis.external_calls) * 3.0
            complexity += len(self.backend_analysis.data_transformations) * 1.0
        
        if self.api_analysis:
            complexity += len(self.api_analysis.endpoints) * 1.0
            complexity += len(self.api_analysis.data_models) * 0.5
        
        self.complexity_score = complexity
        return complexity
    
    def estimate_hours(self) -> float:
        """Estima las horas necesarias para la migración"""
        base_hours = 4.0  # Horas base por pantalla
        complexity_factor = self.calculate_complexity() * 0.5
        
        self.estimated_hours = base_hours + complexity_factor
        return self.estimated_hours
    
    def is_complete(self) -> bool:
        """Verifica si el análisis está completo"""
        return (self.status == AnalysisStatus.COMPLETED and
                self.frontend_analysis is not None and
                self.backend_analysis is not None and
                self.api_analysis is not None)
    
    def get_summary(self) -> Dict[str, Any]:
        """Obtiene un resumen del análisis"""
        return {
            "id": self.id,
            "screen_id": self.screen_id,
            "status": self.status.value,
            "complexity_score": self.complexity_score,
            "estimated_hours": self.estimated_hours,
            "components": {
                "frontend": self.frontend_analysis is not None,
                "backend": self.backend_analysis is not None,
                "api": self.api_analysis is not None
            },
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None
        }