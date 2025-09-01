from sqlalchemy import Column, String, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from ...database import Base

class AIAnalysisResult(Base):
    """Entidad para almacenar resultados de análisis IA de ficheros .SCR"""
    
    __tablename__ = "ai_analysis_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    file_analysis_id = Column(String(255), ForeignKey('nsdk_file_analyses.id'), nullable=False)
    
    # Metadatos del análisis
    analysis_timestamp = Column(DateTime, default=datetime.utcnow)
    analysis_version = Column(String(20), default="1.0")
    
    # Resultado del análisis (JSON)
    analysis_summary = Column(Text)
    file_type = Column(String(50))  # screen|form|report|utility
    complexity = Column(String(20))  # low|medium|high
    estimated_hours = Column(String(10))
    
    # Análisis frontend (JSON)
    frontend_analysis = Column(JSON)
    
    # Análisis backend (JSON)
    backend_analysis = Column(JSON)
    
    # Notas y problemas potenciales (JSON)
    migration_notes = Column(JSON)
    potential_issues = Column(JSON)
    
    # Respuesta completa de la IA (para debugging)
    raw_ai_response = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, file_analysis_id: str, analysis_data: dict, raw_response: str = None):
        self.file_analysis_id = file_analysis_id
        self.analysis_summary = analysis_data.get('analysis_summary')
        self.file_type = analysis_data.get('file_type')
        self.complexity = analysis_data.get('complexity')
        self.estimated_hours = str(analysis_data.get('estimated_hours', 0))
        self.frontend_analysis = analysis_data.get('frontend')
        self.backend_analysis = analysis_data.get('backend')
        self.migration_notes = analysis_data.get('migration_notes')
        self.potential_issues = analysis_data.get('potential_issues')
        self.raw_ai_response = raw_response
        self.analysis_version = analysis_data.get('analysis_version', '1.0')
    
    def to_dict(self) -> dict:
        """Convierte la entidad a diccionario"""
        import json
        
        # Función helper para parsear JSON strings
        def parse_json_field(field):
            if isinstance(field, str):
                try:
                    return json.loads(field)
                except (json.JSONDecodeError, TypeError):
                    return []
            return field or []
        
        # Procesar frontend_analysis
        frontend_analysis = self.frontend_analysis
        if isinstance(frontend_analysis, str):
            try:
                frontend_analysis = json.loads(frontend_analysis)
            except (json.JSONDecodeError, TypeError):
                frontend_analysis = {}
        
        # Procesar backend_analysis
        backend_analysis = self.backend_analysis
        if isinstance(backend_analysis, str):
            try:
                backend_analysis = json.loads(backend_analysis)
            except (json.JSONDecodeError, TypeError):
                backend_analysis = {}
        
        # Procesar frontend_analysis para asegurar que dependencies sea un array
        if isinstance(frontend_analysis, dict) and 'dependencies' in frontend_analysis:
            if isinstance(frontend_analysis['dependencies'], str):
                try:
                    frontend_analysis['dependencies'] = json.loads(frontend_analysis['dependencies'])
                except (json.JSONDecodeError, TypeError):
                    frontend_analysis['dependencies'] = []
            elif not isinstance(frontend_analysis['dependencies'], list):
                frontend_analysis['dependencies'] = []
        
        return {
            'id': self.id,
            'file_analysis_id': self.file_analysis_id,
            'analysis_timestamp': self.analysis_timestamp.isoformat() if self.analysis_timestamp else None,
            'analysis_version': self.analysis_version,
            'analysis_summary': self.analysis_summary,
            'file_type': self.file_type,
            'complexity': self.complexity,
            'estimated_hours': self.estimated_hours,
            'frontend': frontend_analysis,
            'backend': backend_analysis,
            'migration_notes': parse_json_field(self.migration_notes),
            'potential_issues': parse_json_field(self.potential_issues),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
