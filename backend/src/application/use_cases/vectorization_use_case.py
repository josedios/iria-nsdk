from typing import List, Dict, Any, Optional
import os
import asyncio
from ...domain.entities import Module, Screen, Configuration
from ...domain.repositories import (
    ModuleRepository, ScreenRepository, ConfigurationRepository,
    GitService, VectorStoreService, LLMService
)

class VectorizationUseCase:
    def __init__(
        self,
        module_repository: ModuleRepository,
        screen_repository: ScreenRepository,
        config_repository: ConfigurationRepository,
        git_service: GitService,
        vector_store_service: VectorStoreService,
        llm_service: LLMService
    ):
        self.module_repository = module_repository
        self.screen_repository = screen_repository
        self.config_repository = config_repository
        self.git_service = git_service
        self.vector_store_service = vector_store_service
        self.llm_service = llm_service
    
    async def vectorize_repositories(self) -> Dict[str, Any]:
        """Vectoriza los repositorios origen y destino"""
        config = await self.config_repository.find_active()
        if not config:
            raise ValueError("No hay configuración activa")
        
        # Inicializar servicios
        await self.vector_store_service.initialize(config.vector_store_config)
        await self.llm_service.initialize(config.llm_config)
        
        # Clonar repositorios
        source_path = "/tmp/source_repo"
        target_path = "/tmp/target_repo"
        
        await self.git_service.clone_repository(config.source_repo, source_path)
        await self.git_service.clone_repository(config.target_repo, target_path)
        
        # Vectorizar código fuente
        source_stats = await self._vectorize_source_code(source_path)
        target_stats = await self._vectorize_target_code(target_path)
        
        # Indexar módulos y pantallas
        modules_stats = await self._index_modules_and_screens(source_path)
        
        return {
            "source_repository": source_stats,
            "target_repository": target_stats,
            "modules_indexed": modules_stats,
            "total_documents": source_stats["documents"] + target_stats["documents"],
            "status": "completed"
        }
    
    async def _vectorize_source_code(self, repo_path: str) -> Dict[str, Any]:
        """Vectoriza el código fuente NSDK"""
        documents = []
        
        # Buscar archivos SCR, NCL y otros relevantes
        scr_files = await self.git_service.list_files(repo_path, "*.SCR")
        ncl_files = await self.git_service.list_files(repo_path, "*.NCL")
        other_files = await self.git_service.list_files(repo_path, "*.txt")
        
        all_files = scr_files + ncl_files + other_files
        
        for file_path in all_files:
            try:
                content = await self.git_service.get_file_content(repo_path, file_path)
                if content:
                    # Crear documento para vectorización
                    doc = {
                        "id": f"source_{file_path.replace('/', '_')}",
                        "content": content,
                        "metadata": {
                            "source": "nsdk_source",
                            "file_path": file_path,
                            "file_type": self._get_file_type(file_path),
                            "repository": "source"
                        }
                    }
                    documents.append(doc)
            except Exception as e:
                print(f"Error procesando {file_path}: {e}")
        
        # Vectorizar documentos
        await self.vector_store_service.add_documents(documents)
        
        return {
            "documents": len(documents),
            "scr_files": len(scr_files),
            "ncl_files": len(ncl_files),
            "other_files": len(other_files)
        }
    
    async def _vectorize_target_code(self, repo_path: str) -> Dict[str, Any]:
        """Vectoriza el código destino Angular/Spring Boot"""
        documents = []
        
        # Buscar archivos Angular y Spring Boot
        angular_files = await self.git_service.list_files(repo_path, "*.ts")
        angular_html = await self.git_service.list_files(repo_path, "*.html")
        spring_files = await self.git_service.list_files(repo_path, "*.java")
        
        all_files = angular_files + angular_html + spring_files
        
        for file_path in all_files:
            try:
                content = await self.git_service.get_file_content(repo_path, file_path)
                if content:
                    doc = {
                        "id": f"target_{file_path.replace('/', '_')}",
                        "content": content,
                        "metadata": {
                            "source": "target_code",
                            "file_path": file_path,
                            "file_type": self._get_file_type(file_path),
                            "repository": "target",
                            "framework": self._get_framework(file_path)
                        }
                    }
                    documents.append(doc)
            except Exception as e:
                print(f"Error procesando {file_path}: {e}")
        
        # Vectorizar documentos
        await self.vector_store_service.add_documents(documents)
        
        return {
            "documents": len(documents),
            "angular_files": len(angular_files + angular_html),
            "spring_files": len(spring_files)
        }
    
    async def _index_modules_and_screens(self, repo_path: str) -> Dict[str, Any]:
        """Indexa módulos y pantallas del repositorio NSDK"""
        modules_created = 0
        screens_created = 0
        
        # Obtener estructura del repositorio
        structure = await self.git_service.get_repository_structure(repo_path)
        
        # Procesar estructura y crear módulos
        for module_path, files in structure.items():
            if self._is_module_directory(files):
                module = await self._create_module_from_path(module_path)
                saved_module = await self.module_repository.save(module)
                modules_created += 1
                
                # Crear pantallas para el módulo
                for file_path in files:
                    if file_path.endswith('.SCR'):
                        screen = await self._create_screen_from_file(
                            file_path, saved_module.id, repo_path
                        )
                        await self.screen_repository.save(screen)
                        screens_created += 1
        
        return {
            "modules_created": modules_created,
            "screens_created": screens_created
        }
    
    async def vectorize_documentation(self, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Vectoriza documentación técnica"""
        documents = []
        
        for doc in docs:
            doc_id = f"doc_{doc['name'].replace(' ', '_')}"
            documents.append({
                "id": doc_id,
                "content": doc["content"],
                "metadata": {
                    "source": "documentation",
                    "doc_type": doc.get("type", "manual"),
                    "title": doc["name"],
                    "language": doc.get("language", "es")
                }
            })
        
        await self.vector_store_service.add_documents(documents)
        
        return {
            "documents_vectorized": len(documents),
            "status": "completed"
        }
    
    async def get_vectorization_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de vectorización"""
        stats = await self.vector_store_service.get_collection_stats()
        
        return {
            "total_documents": stats.get("total_documents", 0),
            "source_documents": stats.get("source_documents", 0),
            "target_documents": stats.get("target_documents", 0),
            "documentation_documents": stats.get("documentation_documents", 0),
            "last_updated": stats.get("last_updated"),
            "collection_size": stats.get("collection_size", 0)
        }
    
    async def search_similar_code(self, query: str, source_type: str = "all") -> List[Dict[str, Any]]:
        """Busca código similar en el vector store"""
        metadata_filter = {}
        
        if source_type != "all":
            metadata_filter["source"] = source_type
        
        results = await self.vector_store_service.hybrid_search(
            query=query,
            metadata_filter=metadata_filter,
            top_k=10
        )
        
        return results
    
    def _get_file_type(self, file_path: str) -> str:
        """Obtiene el tipo de archivo basado en la extensión"""
        extension = os.path.splitext(file_path)[1].lower()
        type_map = {
            '.scr': 'nsdk_screen',
            '.ncl': 'nsdk_logic',
            '.ts': 'typescript',
            '.html': 'html',
            '.java': 'java',
            '.txt': 'text'
        }
        return type_map.get(extension, 'unknown')
    
    def _get_framework(self, file_path: str) -> str:
        """Obtiene el framework basado en la ruta del archivo"""
        if '/angular/' in file_path or file_path.endswith('.ts'):
            return 'angular'
        elif '/spring/' in file_path or file_path.endswith('.java'):
            return 'spring_boot'
        return 'unknown'
    
    def _is_module_directory(self, files: List[str]) -> bool:
        """Verifica si un directorio contiene archivos de módulo"""
        return any(file.endswith('.SCR') for file in files)
    
    async def _create_module_from_path(self, module_path: str) -> Module:
        """Crea un módulo basado en la ruta"""
        module_name = os.path.basename(module_path)
        
        return Module(
            id=None,
            name=module_name,
            path=module_path,
            description=f"Módulo {module_name} migrado desde NSDK"
        )
    
    async def _create_screen_from_file(self, file_path: str, module_id: str, repo_path: str) -> Screen:
        """Crea una pantalla basada en un archivo SCR"""
        screen_name = os.path.basename(file_path)
        content = await self.git_service.get_file_content(repo_path, file_path)
        
        return Screen(
            id=None,
            name=screen_name,
            file_path=file_path,
            module_id=module_id,
            scr_content=content
        )