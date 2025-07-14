from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Tuple
from ..entities import VectorStoreConfig

class VectorStoreService(ABC):
    """Puerto (interface) para servicios de Vector Store"""
    
    @abstractmethod
    async def initialize(self, config: VectorStoreConfig) -> bool:
        """Inicializa el vector store con la configuración"""
        pass
    
    @abstractmethod
    async def add_document(self, doc_id: str, content: str, metadata: Dict[str, Any]) -> bool:
        """Añade un documento al vector store"""
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """Añade múltiples documentos al vector store"""
        pass
    
    @abstractmethod
    async def search_similar(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Busca documentos similares a la consulta"""
        pass
    
    @abstractmethod
    async def search_by_metadata(self, metadata_filter: Dict[str, Any], 
                               top_k: int = 10) -> List[Dict[str, Any]]:
        """Busca documentos por metadatos"""
        pass
    
    @abstractmethod
    async def update_document(self, doc_id: str, content: str, 
                            metadata: Dict[str, Any]) -> bool:
        """Actualiza un documento existente"""
        pass
    
    @abstractmethod
    async def delete_document(self, doc_id: str) -> bool:
        """Elimina un documento del vector store"""
        pass
    
    @abstractmethod
    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un documento por su ID"""
        pass
    
    @abstractmethod
    async def clear_collection(self) -> bool:
        """Limpia toda la colección"""
        pass
    
    @abstractmethod
    async def get_collection_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de la colección"""
        pass
    
    @abstractmethod
    async def create_index(self, field_name: str) -> bool:
        """Crea un índice para un campo específico"""
        pass
    
    @abstractmethod
    async def hybrid_search(self, query: str, metadata_filter: Dict[str, Any], 
                          top_k: int = 10) -> List[Dict[str, Any]]:
        """Realiza una búsqueda híbrida combinando similitud y metadatos"""
        pass
    
    @abstractmethod
    async def get_similar_code(self, code_snippet: str, language: str, 
                             top_k: int = 5) -> List[Dict[str, Any]]:
        """Busca código similar en el repositorio"""
        pass