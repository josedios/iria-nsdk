from pydantic import BaseModel
from typing import Optional, Any
from uuid import UUID
from datetime import datetime

class ConfigurationDTO(BaseModel):
    id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    config_data: Any
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class CreateConfigurationDTO(BaseModel):
    """DTO para crear nuevas configuraciones (sin ID)"""
    name: str
    description: Optional[str] = None
    config_data: Any

class UpdateConfigurationDTO(BaseModel):
    """DTO para actualizar configuraciones existentes"""
    name: str
    description: Optional[str] = None
    config_data: Any