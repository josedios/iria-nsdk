from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import Analysis, AnalysisStatus

class AnalysisRepository(ABC):
    """Puerto (interface) para la gestión de análisis"""
    
    @abstractmethod
    async def save(self, analysis: Analysis) -> Analysis:
        """Guarda un análisis en la base de datos"""
        pass
    
    @abstractmethod
    async def find_by_id(self, analysis_id: str) -> Optional[Analysis]:
        """Busca un análisis por su ID"""
        pass
    
    @abstractmethod
    async def find_all(self) -> List[Analysis]:
        """Obtiene todos los análisis"""
        pass
    
    @abstractmethod
    async def find_by_screen_id(self, screen_id: str) -> Optional[Analysis]:
        """Busca un análisis por ID de pantalla"""
        pass
    
    @abstractmethod
    async def find_by_status(self, status: AnalysisStatus) -> List[Analysis]:
        """Busca análisis por estado"""
        pass
    
    @abstractmethod
    async def update(self, analysis: Analysis) -> Analysis:
        """Actualiza un análisis existente"""
        pass
    
    @abstractmethod
    async def delete(self, analysis_id: str) -> bool:
        """Elimina un análisis por su ID"""
        pass
    
    @abstractmethod
    async def get_statistics(self) -> dict:
        """Obtiene estadísticas de los análisis"""
        pass