from dataclasses import dataclass
from typing import Optional, Dict, Any
from enum import Enum

class LLMProviderDTO(Enum):
    OPENAI = "openai"
    OLLAMA = "ollama"
    MISTRAL = "mistral"

class VectorStoreTypeDTO(Enum):
    FAISS = "faiss"
    QDRANT = "qdrant"
    CHROMA = "chroma"

@dataclass
class RepositoryConfigDTO:
    url: str
    branch: str = "main"
    username: Optional[str] = None
    token: Optional[str] = None
    ssh_key: Optional[str] = None

@dataclass
class LLMConfigDTO:
    provider: LLMProviderDTO
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model_name: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 4000
    additional_params: Dict[str, Any] = None

@dataclass
class VectorStoreConfigDTO:
    type: VectorStoreTypeDTO
    connection_string: Optional[str] = None
    collection_name: str = "nsdk_migration"
    embedding_model: str = "text-embedding-3-small"
    dimension: int = 1536
    additional_params: Dict[str, Any] = None

@dataclass
class ConfigurationCreateDTO:
    name: str
    source_repo: RepositoryConfigDTO
    target_repo: RepositoryConfigDTO
    llm_config: LLMConfigDTO
    vector_store_config: VectorStoreConfigDTO

@dataclass
class ConfigurationUpdateDTO:
    name: Optional[str] = None
    source_repo: Optional[RepositoryConfigDTO] = None
    target_repo: Optional[RepositoryConfigDTO] = None
    llm_config: Optional[LLMConfigDTO] = None
    vector_store_config: Optional[VectorStoreConfigDTO] = None

@dataclass
class ConfigurationResponseDTO:
    id: str
    name: str
    source_repo: RepositoryConfigDTO
    target_repo: RepositoryConfigDTO
    llm_config: LLMConfigDTO
    vector_store_config: VectorStoreConfigDTO
    is_active: bool
    created_at: str
    updated_at: str