from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..entities import RepositoryConfig

class GitService(ABC):
    """Puerto (interface) para servicios de Git"""
    
    @abstractmethod
    async def clone_repository(self, config: RepositoryConfig, local_path: str) -> bool:
        """Clona un repositorio en una ruta local"""
        pass
    
    @abstractmethod
    async def pull_repository(self, local_path: str) -> bool:
        """Actualiza un repositorio local"""
        pass
    
    @abstractmethod
    async def create_branch(self, local_path: str, branch_name: str) -> bool:
        """Crea una nueva rama"""
        pass
    
    @abstractmethod
    async def checkout_branch(self, local_path: str, branch_name: str) -> bool:
        """Cambia a una rama específica"""
        pass
    
    @abstractmethod
    async def commit_changes(self, local_path: str, message: str) -> bool:
        """Hace commit de los cambios"""
        pass
    
    @abstractmethod
    async def push_changes(self, local_path: str, branch_name: str) -> bool:
        """Sube los cambios al repositorio remoto"""
        pass
    
    @abstractmethod
    async def get_file_content(self, local_path: str, file_path: str) -> Optional[str]:
        """Obtiene el contenido de un archivo"""
        pass
    
    @abstractmethod
    async def write_file(self, local_path: str, file_path: str, content: str) -> bool:
        """Escribe contenido en un archivo"""
        pass
    
    @abstractmethod
    async def list_files(self, local_path: str, pattern: str = "*") -> List[str]:
        """Lista archivos que coinciden con un patrón"""
        pass
    
    @abstractmethod
    async def get_repository_structure(self, local_path: str) -> Dict[str, Any]:
        """Obtiene la estructura del repositorio"""
        pass
    
    @abstractmethod
    async def check_repository_exists(self, local_path: str) -> bool:
        """Verifica si el repositorio existe localmente"""
        pass
    
    @abstractmethod
    async def get_branch_list(self, local_path: str) -> List[str]:
        """Obtiene la lista de ramas"""
        pass
    
    @abstractmethod
    async def get_commit_history(self, local_path: str, limit: int = 10) -> List[Dict[str, str]]:
        """Obtiene el historial de commits"""
        pass