from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum
from datetime import datetime
import uuid

class LLMProvider(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    MISTRAL = "mistral"

class VectorStoreType(Enum):
    FAISS = "faiss"
    QDRANT = "qdrant"
    CHROMA = "chroma"

@dataclass
class RepositoryConfig:
    url: str
    branch: str = "main"
    username: Optional[str] = None
    token: Optional[str] = None
    ssh_key: Optional[str] = None

@dataclass
class LLMConfig:
    provider: LLMProvider
    api_key: Optional[str] = None
    base_url: Optional[str] = None  # Para Ollama
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4000
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}

@dataclass
class VectorStoreConfig:
    type: VectorStoreType
    connection_string: Optional[str] = None
    collection_name: str = "nsdk_migration"
    embedding_model: str = "text-embedding-3-small"
    dimension: int = 1536
    additional_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.additional_params is None:
            self.additional_params = {}

@dataclass
class Configuration:
    id: str
    name: str
    source_repo: RepositoryConfig
    target_repo: RepositoryConfig
    llm_config: LLMConfig
    vector_store_config: VectorStoreConfig
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    def update(self):
        """Actualiza la fecha de modificación"""
        self.updated_at = datetime.utcnow()
    
    def validate(self) -> bool:
        """Valida que la configuración esté completa"""
        if not self.source_repo.url or not self.target_repo.url:
            return False
        
        if self.llm_config.provider == LLMProvider.OPENAI and not self.llm_config.api_key:
            return False
        
        if self.llm_config.provider == LLMProvider.OLLAMA and not self.llm_config.base_url:
            return False
        
        if self.llm_config.provider == LLMProvider.MISTRAL and not self.llm_config.api_key:
            return False
        
        return True
    
    def get_git_credentials(self, repo_type: str) -> Dict[str, Any]:
        """Obtiene las credenciales para Git según el tipo de repositorio"""
        repo = self.source_repo if repo_type == "source" else self.target_repo
        
        credentials = {}
        if repo.username and repo.token:
            credentials["username"] = repo.username
            credentials["token"] = repo.token
        elif repo.ssh_key:
            credentials["ssh_key"] = repo.ssh_key
        
        return credentials