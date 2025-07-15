from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID
from datetime import datetime

class ConfigurationDTO(BaseModel):
    id: Optional[UUID]
    name: str
    description: Optional[str] = None
    config_data: Any
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True