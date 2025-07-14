from typing import List, Optional
from ...domain.entities import Configuration, LLMProvider, VectorStoreType, RepositoryConfig, LLMConfig, VectorStoreConfig
from ...domain.repositories import ConfigurationRepository
from ..dto.configuration_dto import (
    ConfigurationCreateDTO, ConfigurationUpdateDTO, ConfigurationResponseDTO,
    LLMProviderDTO, VectorStoreTypeDTO, RepositoryConfigDTO, LLMConfigDTO, VectorStoreConfigDTO
)

class ConfigurationUseCase:
    def __init__(self, config_repository: ConfigurationRepository):
        self.config_repository = config_repository
    
    async def create_configuration(self, dto: ConfigurationCreateDTO) -> ConfigurationResponseDTO:
        """Crea una nueva configuración"""
        # Convertir DTO a entidades del dominio
        source_repo = RepositoryConfig(
            url=dto.source_repo.url,
            branch=dto.source_repo.branch,
            username=dto.source_repo.username,
            token=dto.source_repo.token,
            ssh_key=dto.source_repo.ssh_key
        )
        
        target_repo = RepositoryConfig(
            url=dto.target_repo.url,
            branch=dto.target_repo.branch,
            username=dto.target_repo.username,
            token=dto.target_repo.token,
            ssh_key=dto.target_repo.ssh_key
        )
        
        llm_config = LLMConfig(
            provider=LLMProvider(dto.llm_config.provider.value),
            api_key=dto.llm_config.api_key,
            base_url=dto.llm_config.base_url,
            model_name=dto.llm_config.model_name,
            temperature=dto.llm_config.temperature,
            max_tokens=dto.llm_config.max_tokens,
            additional_params=dto.llm_config.additional_params or {}
        )
        
        vector_store_config = VectorStoreConfig(
            type=VectorStoreType(dto.vector_store_config.type.value),
            connection_string=dto.vector_store_config.connection_string,
            collection_name=dto.vector_store_config.collection_name,
            embedding_model=dto.vector_store_config.embedding_model,
            dimension=dto.vector_store_config.dimension,
            additional_params=dto.vector_store_config.additional_params or {}
        )
        
        configuration = Configuration(
            id=None,
            name=dto.name,
            source_repo=source_repo,
            target_repo=target_repo,
            llm_config=llm_config,
            vector_store_config=vector_store_config
        )
        
        # Validar configuración
        if not configuration.validate():
            raise ValueError("La configuración no es válida")
        
        # Guardar configuración
        saved_config = await self.config_repository.save(configuration)
        
        return self._to_response_dto(saved_config)
    
    async def get_configuration(self, config_id: str) -> Optional[ConfigurationResponseDTO]:
        """Obtiene una configuración por ID"""
        config = await self.config_repository.find_by_id(config_id)
        if not config:
            return None
        
        return self._to_response_dto(config)
    
    async def get_all_configurations(self) -> List[ConfigurationResponseDTO]:
        """Obtiene todas las configuraciones"""
        configs = await self.config_repository.find_all()
        return [self._to_response_dto(config) for config in configs]
    
    async def get_active_configuration(self) -> Optional[ConfigurationResponseDTO]:
        """Obtiene la configuración activa"""
        config = await self.config_repository.find_active()
        if not config:
            return None
        
        return self._to_response_dto(config)
    
    async def update_configuration(self, config_id: str, dto: ConfigurationUpdateDTO) -> Optional[ConfigurationResponseDTO]:
        """Actualiza una configuración existente"""
        config = await self.config_repository.find_by_id(config_id)
        if not config:
            return None
        
        # Actualizar campos si se proporcionan
        if dto.name:
            config.name = dto.name
        
        if dto.source_repo:
            config.source_repo = RepositoryConfig(
                url=dto.source_repo.url,
                branch=dto.source_repo.branch,
                username=dto.source_repo.username,
                token=dto.source_repo.token,
                ssh_key=dto.source_repo.ssh_key
            )
        
        if dto.target_repo:
            config.target_repo = RepositoryConfig(
                url=dto.target_repo.url,
                branch=dto.target_repo.branch,
                username=dto.target_repo.username,
                token=dto.target_repo.token,
                ssh_key=dto.target_repo.ssh_key
            )
        
        if dto.llm_config:
            config.llm_config = LLMConfig(
                provider=LLMProvider(dto.llm_config.provider.value),
                api_key=dto.llm_config.api_key,
                base_url=dto.llm_config.base_url,
                model_name=dto.llm_config.model_name,
                temperature=dto.llm_config.temperature,
                max_tokens=dto.llm_config.max_tokens,
                additional_params=dto.llm_config.additional_params or {}
            )
        
        if dto.vector_store_config:
            config.vector_store_config = VectorStoreConfig(
                type=VectorStoreType(dto.vector_store_config.type.value),
                connection_string=dto.vector_store_config.connection_string,
                collection_name=dto.vector_store_config.collection_name,
                embedding_model=dto.vector_store_config.embedding_model,
                dimension=dto.vector_store_config.dimension,
                additional_params=dto.vector_store_config.additional_params or {}
            )
        
        config.update()
        
        # Validar configuración actualizada
        if not config.validate():
            raise ValueError("La configuración actualizada no es válida")
        
        updated_config = await self.config_repository.update(config)
        return self._to_response_dto(updated_config)
    
    async def delete_configuration(self, config_id: str) -> bool:
        """Elimina una configuración"""
        return await self.config_repository.delete(config_id)
    
    async def set_active_configuration(self, config_id: str) -> bool:
        """Establece una configuración como activa"""
        return await self.config_repository.set_active(config_id)
    
    def _to_response_dto(self, config: Configuration) -> ConfigurationResponseDTO:
        """Convierte una entidad Configuration a DTO de respuesta"""
        return ConfigurationResponseDTO(
            id=config.id,
            name=config.name,
            source_repo=RepositoryConfigDTO(
                url=config.source_repo.url,
                branch=config.source_repo.branch,
                username=config.source_repo.username,
                token=config.source_repo.token,
                ssh_key=config.source_repo.ssh_key
            ),
            target_repo=RepositoryConfigDTO(
                url=config.target_repo.url,
                branch=config.target_repo.branch,
                username=config.target_repo.username,
                token=config.target_repo.token,
                ssh_key=config.target_repo.ssh_key
            ),
            llm_config=LLMConfigDTO(
                provider=LLMProviderDTO(config.llm_config.provider.value),
                api_key=config.llm_config.api_key,
                base_url=config.llm_config.base_url,
                model_name=config.llm_config.model_name,
                temperature=config.llm_config.temperature,
                max_tokens=config.llm_config.max_tokens,
                additional_params=config.llm_config.additional_params
            ),
            vector_store_config=VectorStoreConfigDTO(
                type=VectorStoreTypeDTO(config.vector_store_config.type.value),
                connection_string=config.vector_store_config.connection_string,
                collection_name=config.vector_store_config.collection_name,
                embedding_model=config.vector_store_config.embedding_model,
                dimension=config.vector_store_config.dimension,
                additional_params=config.vector_store_config.additional_params
            ),
            is_active=config.is_active,
            created_at=config.created_at.isoformat(),
            updated_at=config.updated_at.isoformat()
        )