from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import Configuration

class ConfigurationRepository(ABC):
    """Puerto (interface) para la gestión de configuraciones"""
    
    @abstractmethod
    async def save(self, configuration: Configuration) -> Configuration:
        """Guarda una configuración en la base de datos"""
        pass
    
    @abstractmethod
    async def find_by_id(self, config_id: str) -> Optional[Configuration]:
        """Busca una configuración por su ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Configuration]:
        """Obtiene todas las configuraciones"""
        pass
    
    @abstractmethod
    async def find_active(self) -> Optional[Configuration]:
        """Obtiene la configuración activa"""
        pass
    
    @abstractmethod
    async def update(self, configuration: Configuration) -> Configuration:
        """Actualiza una configuración existente"""
        pass
    
    @abstractmethod
    async def delete(self, config_id: str) -> bool:
        """Elimina una configuración por su ID"""
        pass
    
    @abstractmethod
    async def set_active(self, config_id: str) -> bool:
        """Establece una configuración como activa"""
        pass
    
    @abstractmethod
    async def find_by_name(self, name: str) -> Optional[Configuration]:
        """Busca una configuración por nombre"""
        pass