from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import Screen, ScreenStatus

class ScreenRepository(ABC):
    """Puerto (interface) para la gestión de pantallas"""
    
    @abstractmethod
    async def save(self, screen: Screen) -> Screen:
        """Guarda una pantalla en la base de datos"""
        pass
    
    @abstractmethod
    async def find_by_id(self, screen_id: str) -> Optional[Screen]:
        """Busca una pantalla por su ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Screen]:
        """Obtiene todas las pantallas"""
        pass
    
    @abstractmethod
    async def find_by_module_id(self, module_id: str) -> List[Screen]:
        """Busca pantallas por ID de módulo"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: ScreenStatus) -> List[Screen]:
        """Busca pantallas por estado"""
        pass
    
    @abstractmethod
    async def find_by_developer(self, developer: str) -> List[Screen]:
        """Busca pantallas asignadas a un desarrollador"""
        pass
    
    @abstractmethod
    async def update(self, screen: Screen) -> Screen:
        """Actualiza una pantalla existente"""
        pass
    
    @abstractmethod
    async def delete(self, screen_id: str) -> bool:
        """Elimina una pantalla por su ID"""
        pass
    
    @abstractmethod
    async def find_by_file_path(self, file_path: str) -> Optional[Screen]:
        """Busca una pantalla por su ruta de archivo"""
        pass
    
    @abstractmethod
    async def get_screens_for_analysis(self) -> List[Screen]:
        """Obtiene pantallas listas para análisis"""
        pass
    
    @abstractmethod
    async def get_screens_for_generation(self) -> List[Screen]:
        """Obtiene pantallas listas para generación"""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> dict:
        """Obtiene estadísticas de las pantallas"""
        pass