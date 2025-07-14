from dataclasses import dataclass
from typing import List, Optional
from enum import Enum
from datetime import datetime
import uuid

class ModuleStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ERROR = "error"

@dataclass
class Module:
    id: str
    name: str
    path: str
    description: Optional[str] = None
    status: ModuleStatus = ModuleStatus.PENDING
    created_at: datetime = None
    updated_at: datetime = None
    screens: List['Screen'] = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
        if self.screens is None:
            self.screens = []
    
    def add_screen(self, screen: 'Screen'):
        self.screens.append(screen)
        self.updated_at = datetime.utcnow()
    
    def get_completion_percentage(self) -> float:
        if not self.screens:
            return 0.0
        
        completed = sum(1 for screen in self.screens if screen.status == ModuleStatus.COMPLETED)
        return (completed / len(self.screens)) * 100
    
    def update_status(self):
        if not self.screens:
            self.status = ModuleStatus.PENDING
            return
        
        if all(screen.status == ModuleStatus.COMPLETED for screen in self.screens):
            self.status = ModuleStatus.COMPLETED
        elif any(screen.status == ModuleStatus.IN_PROGRESS for screen in self.screens):
            self.status = ModuleStatus.IN_PROGRESS
        elif any(screen.status == ModuleStatus.ERROR for screen in self.screens):
            self.status = ModuleStatus.ERROR
        else:
            self.status = ModuleStatus.PENDING
        
        self.updated_at = datetime.utcnow()