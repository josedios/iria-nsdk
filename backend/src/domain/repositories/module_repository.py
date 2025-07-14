from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import Module, ModuleStatus

class ModuleRepository(ABC):
    """Puerto (interface) para la gestión de módulos"""
    
    @abstractmethod
    async def save(self, module: Module) -> Module:
        """Guarda un módulo en la base de datos"""
        pass
    
    @abstractmethod
    async def find_by_id(self, module_id: str) -> Optional[Module]:
        """Busca un módulo por su ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Module]:
        """Obtiene todos los módulos"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: ModuleStatus) -> List[Module]:
        """Busca módulos por estado"""
        pass
    
    @abstractmethod
    async def update(self, module: Module) -> Module:
        """Actualiza un módulo existente"""
        pass
    
    @abstractmethod
    async def delete(self, module_id: str) -> bool:
        """Elimina un módulo por su ID"""
        pass
    
    @abstractmethod
    async def find_by_path(self, path: str) -> Optional[Module]:
        """Busca un módulo por su ruta"""
        pass
    
    @abstractmethod
    async def get_modules_tree(self) -> List[dict]:
        """Obtiene la estructura jerárquica de módulos"""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> dict:
        """Obtiene estadísticas de los módulos"""
        pass