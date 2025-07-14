from dataclasses import dataclass
from typing import Optional
from enum import Enum
from datetime import datetime
import uuid

class ScreenStatus(Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    GENERATING = "generating"
    GENERATED = "generated"
    MIGRATED = "migrated"
    ERROR = "error"

@dataclass
class Screen:
    id: str
    name: str
    file_path: str
    module_id: str
    scr_content: Optional[str] = None
    status: ScreenStatus = ScreenStatus.PENDING
    assigned_developer: Optional[str] = None
    analysis_id: Optional[str] = None
    generated_branch: Optional[str] = None
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def update_status(self, new_status: ScreenStatus):
        self.status = new_status
        self.updated_at = datetime.utcnow()
    
    def assign_developer(self, developer: str):
        self.assigned_developer = developer
        self.updated_at = datetime.utcnow()
    
    def set_analysis(self, analysis_id: str):
        self.analysis_id = analysis_id
        self.status = ScreenStatus.ANALYZED
        self.updated_at = datetime.utcnow()
    
    def set_generated_branch(self, branch_name: str):
        self.generated_branch = branch_name
        self.status = ScreenStatus.GENERATED
        self.updated_at = datetime.utcnow()
    
    def get_display_name(self) -> str:
        """Obtiene el nombre para mostrar en la UI"""
        return self.name.replace('.SCR', '').replace('_', ' ').title()
    
    def is_ready_for_analysis(self) -> bool:
        """Verifica si la pantalla está lista para ser analizada"""
        return self.status == ScreenStatus.PENDING and self.scr_content is not None
    
    def is_ready_for_generation(self) -> bool:
        """Verifica si la pantalla está lista para generar código"""
        return self.status == ScreenStatus.ANALYZED and self.analysis_id is not None