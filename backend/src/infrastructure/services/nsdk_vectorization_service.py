import os
import re
import tempfile
import shutil
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from git import Repo, GitCommandError
from abc import ABC, abstractmethod
from uuid import UUID

from ...domain.entities.nsdk_file import NSDKFile, NSDKFileType, NSDKFileStatus
from ...domain.entities.vectorization_batch import VectorizationBatch, VectorizationBatchStatus, VectorizationBatchType
from .vector_store_service_impl import VectorStoreServiceImpl
from .llm_service_impl import LLMServiceImpl
from .repository_manager_service import RepositoryManagerService

logger = logging.getLogger(__name__)

class RepositoryVectorizationService(ABC):
    """Servicio base abstracto para vectorización de repositorios"""
    
    def __init__(self, vector_store_service: VectorStoreServiceImpl, llm_service: LLMServiceImpl):
        self.vector_store_service = vector_store_service
        self.llm_service = llm_service
    
    @abstractmethod
    async def vectorize_repository(self, repo_path: str, batch: VectorizationBatch) -> VectorizationBatch:
        """Vectoriza un repositorio del tipo específico"""
        pass
    
    @abstractmethod
    def discover_files(self, repo_path: str) -> List[str]:
        """Descubre archivos relevantes para vectorización"""
        pass
    
    @abstractmethod
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """Procesa un archivo individual"""
        pass

class NSDKVectorizationService(RepositoryVectorizationService):
    """Servicio especializado para vectorizar archivos NSDK (.SCR, .NCL, .INC, .PRG)"""
    
    def __init__(self, vector_store_service: VectorStoreServiceImpl, llm_service: LLMServiceImpl):
        super().__init__(vector_store_service, llm_service)
        
        # Patrones para detectar archivos NSDK
        self.nsdk_file_patterns = {
            'scr': r'\.(scr|SCR)$',
            'ncl': r'\.(ncl|NCL)$',
            'inc': r'\.(inc|INC)$',
            'prg': r'\.(prg|PRG)$'
        }
        
        # Patrones para extraer información de archivos NSDK
        self.nsdk_content_patterns = {
            'scr': {
                'screen_name': r'SCREEN\s+(\w+)',
                'fields': r'FIELD\s+(\w+)\s+(\w+)',
                'buttons': r'BUTTON\s+(\w+)',
                'validations': r'VALIDATE\s+(.+)',
                'events': r'ON\s+(\w+)\s+(.+)'
            },
            'ncl': {
                'module_name': r'MODULE\s+(\w+)',
                'functions': r'FUNCTION\s+(\w+)',
                'variables': r'VAR\s+(\w+)',
                'sql_queries': r'SELECT\s+(.+)',
                'api_calls': r'CALL\s+(\w+)'
            }
        }
    
    def discover_files(self, repo_path: str) -> List[str]:
        """Descubre archivos NSDK en el directorio"""
        nsdk_files = []
        root_path = Path(repo_path)
        
        logger.info(f"Buscando archivos NSDK en: {root_path}")
        
        if not root_path.exists():
            logger.warning(f"El directorio de búsqueda no existe: {root_path}")
            return []
        
        # Buscar archivos NSDK recursivamente
        for file_path in root_path.rglob('*'):
            if file_path.is_file():
                for file_type, pattern in self.nsdk_file_patterns.items():
                    if re.search(pattern, file_path.name):
                        nsdk_files.append(str(file_path))
                        logger.debug(f"Archivo NSDK encontrado: {file_path.name} (tipo: {file_type})")
                        break
        
        logger.info(f"Total de archivos NSDK encontrados: {len(nsdk_files)}")
        return nsdk_files
    
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """Procesa un archivo NSDK individual"""
        try:
            # Leer contenido del archivo
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extraer metadatos
            metadata = self._extract_nsdk_metadata(file_path, content)
            
            # Vectorizar contenido
            vectorization_text = self._create_vectorization_text(file_path, content, metadata)
            embedding = await self.llm_service.get_embedding(vectorization_text)
            
            return {
                'success': True,
                'metadata': metadata,
                'embedding': embedding,
                'content_preview': content[:1000]  # Primeros 1000 caracteres
            }
            
        except Exception as e:
            logger.error(f"Error procesando archivo NSDK {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def vectorize_repository(self, repo_path: str, batch: VectorizationBatch) -> VectorizationBatch:
        """Vectoriza un repositorio NSDK completo"""
        try:
            # Descubrir archivos
            nsdk_files = self.discover_files(repo_path)
            
            if not nsdk_files:
                logger.warning("No se encontraron archivos NSDK para vectorizar")
                batch.fail_processing("No se encontraron archivos NSDK")
                return batch
            
            # Añadir archivos al lote
            for file_path in nsdk_files:
                file_id = str(hash(file_path))
                batch.add_file(file_id)
            
            # Procesar archivos
            batch.start_processing()
            logger.info(f"Iniciando procesamiento de {len(nsdk_files)} archivos NSDK")
            
            for i, file_path in enumerate(nsdk_files):
                try:
                    logger.info(f"Procesando archivo {i+1}/{len(nsdk_files)}: {file_path}")
                    
                    result = await self.process_file(file_path)
                    file_id = str(hash(file_path))
                    
                    if result['success']:
                        batch.mark_file_processed(file_id, success=True)
                        logger.info(f"Archivo {Path(file_path).name} procesado exitosamente")
                    else:
                        batch.mark_file_processed(file_id, success=False)
                        logger.error(f"Error procesando {Path(file_path).name}: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"Error procesando archivo {file_path}: {str(e)}")
                    file_id = str(hash(file_path))
                    batch.mark_file_processed(file_id, success=False)
            
            # Completar lote
            if batch.failed_files > 0:
                logger.warning(f"Fallaron {batch.failed_files} archivos, marcando lote como fallido")
                batch.fail_processing(f"Fallaron {batch.failed_files} archivos")
            else:
                logger.info("Todos los archivos procesados exitosamente")
                batch.complete_processing()
            
            return batch
            
        except Exception as e:
            logger.error(f"Error en vectorización NSDK: {str(e)}")
            batch.fail_processing(str(e))
            return batch
    
    def _extract_nsdk_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extrae metadatos del contenido NSDK"""
        metadata = {}
        file_name = Path(file_path).name
        
        # Determinar tipo de archivo
        file_type = 'unknown'
        for ext, pattern in self.nsdk_file_patterns.items():
            if re.search(pattern, file_name):
                file_type = ext
                break
        
        # Extraer información específica del tipo
        if file_type in self.nsdk_content_patterns:
            patterns = self.nsdk_content_patterns[file_type]
            for key, pattern in patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    metadata[key] = matches
        
        # Información general
        metadata['line_count'] = len(content.split('\n'))
        metadata['char_count'] = len(content)
        metadata['file_type'] = file_type
        metadata['file_name'] = file_name
        
        return metadata
    
    def _create_vectorization_text(self, file_path: str, content: str, metadata: Dict[str, Any]) -> str:
        """Crea texto optimizado para vectorización"""
        text_parts = []
        
        # Nombre del archivo
        text_parts.append(f"Archivo: {metadata['file_name']}")
        
        # Tipo de archivo
        text_parts.append(f"Tipo: {metadata['file_type'].upper()}")
        
        # Contenido del archivo (limitado para evitar tokens excesivos)
        lines = content.split('\n')[:2000]
        content_preview = '\n'.join(lines)
        text_parts.append(f"Contenido:\n{content_preview}")
        
        # Metadatos extraídos
        for key, value in metadata.items():
            if key not in ['line_count', 'char_count', 'file_type', 'file_name']:
                text_parts.append(f"{key}: {value}")
        
        return '\n\n'.join(text_parts)

class AngularVectorizationService(RepositoryVectorizationService):
    """Servicio especializado para vectorizar repositorios Angular"""
    
    def __init__(self, vector_store_service: VectorStoreServiceImpl, llm_service: LLMServiceImpl):
        super().__init__(vector_store_service, llm_service)
        
        # Patrones para detectar archivos Angular
        self.angular_file_patterns = {
            'typescript': r'\.(ts|TS)$',
            'javascript': r'\.(js|JS)$',
            'html': r'\.(html|HTML|htm|HTM)$',
            'css': r'\.(css|CSS|scss|SCSS|sass|SASS|less|LESS)$',
            'json': r'\.(json|JSON)$'
        }
        
        # Patrones para extraer información de archivos Angular
        self.angular_content_patterns = {
            'typescript': {
                'class_name': r'class\s+(\w+)',
                'interface_name': r'interface\s+(\w+)',
                'function_name': r'function\s+(\w+)|(\w+)\s*\([^)]*\)\s*[:{=]',
                'imports': r'import\s+([^;]+)',
                'decorators': r'@(\w+)',
                'component_name': r'selector:\s*[\'"]([^\'"]+)[\'"]',
                'angular_modules': r'@NgModule|@Component|@Injectable|@Directive'
            },
            'html': {
                'tags': r'<(\w+)',
                'attributes': r'(\w+)=["\'][^"\']*["\']',
                'angular_directives': r'(\*ng[A-Za-z]+|ng[A-Z][a-z]+)',
                'event_bindings': r'\(([^)]+)\)',
                'interpolation': r'\{\{([^}]+)\}\}'
            }
        }
    
    def discover_files(self, repo_path: str) -> List[str]:
        """Descubre archivos Angular en el directorio"""
        angular_files = []
        root_path = Path(repo_path)
        
        logger.info(f"Buscando archivos Angular en: {root_path}")
        
        if not root_path.exists():
            logger.warning(f"El directorio de búsqueda no existe: {root_path}")
            return []
        
        # Buscar archivos Angular recursivamente
        for file_path in root_path.rglob('*'):
            if file_path.is_file():
                # Excluir node_modules y otros directorios no relevantes
                if any(part in ['node_modules', '.git', 'dist', 'build'] for part in file_path.parts):
                    continue
                    
                for file_type, pattern in self.angular_file_patterns.items():
                    if re.search(pattern, file_path.name):
                        angular_files.append(str(file_path))
                        logger.debug(f"Archivo Angular encontrado: {file_path.name} (tipo: {file_type})")
                        break
        
        logger.info(f"Total de archivos Angular encontrados: {len(angular_files)}")
        return angular_files
    
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """Procesa un archivo Angular individual"""
        try:
            # Leer contenido del archivo
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extraer metadatos
            metadata = self._extract_angular_metadata(file_path, content)
            
            # Vectorizar contenido
            vectorization_text = self._create_vectorization_text(file_path, content, metadata)
            embedding = await self.llm_service.get_embedding(vectorization_text)
            
            return {
                'success': True,
                'metadata': metadata,
                'embedding': embedding,
                'content_preview': content[:1000]  # Primeros 1000 caracteres
            }
            
        except Exception as e:
            logger.error(f"Error procesando archivo Angular {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def vectorize_repository(self, repo_path: str, batch: VectorizationBatch) -> VectorizationBatch:
        """Vectoriza un repositorio Angular completo"""
        try:
            # Descubrir archivos
            angular_files = self.discover_files(repo_path)
            
            if not angular_files:
                logger.warning("No se encontraron archivos Angular para vectorizar")
                batch.fail_processing("No se encontraron archivos Angular")
                return batch
            
            # Añadir archivos al lote
            for file_path in angular_files:
                file_id = str(hash(file_path))
                batch.add_file(file_id)
            
            # Procesar archivos
            batch.start_processing()
            logger.info(f"Iniciando procesamiento de {len(angular_files)} archivos Angular")
            
            for i, file_path in enumerate(angular_files):
                try:
                    logger.info(f"Procesando archivo {i+1}/{len(angular_files)}: {file_path}")
                    
                    result = await self.process_file(file_path)
                    file_id = str(hash(file_path))
                    
                    if result['success']:
                        batch.mark_file_processed(file_id, success=True)
                        logger.info(f"Archivo {Path(file_path).name} procesado exitosamente")
                    else:
                        batch.mark_file_processed(file_id, success=False)
                        logger.error(f"Error procesando {Path(file_path).name}: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"Error procesando archivo {file_path}: {str(e)}")
                    file_id = str(hash(file_path))
                    batch.mark_file_processed(file_id, success=False)
            
            # Completar lote
            if batch.failed_files > 0:
                logger.warning(f"Fallaron {batch.failed_files} archivos, marcando lote como fallido")
                batch.fail_processing(f"Fallaron {batch.failed_files} archivos")
            else:
                logger.info("Todos los archivos procesados exitosamente")
                batch.complete_processing()
            
            return batch
            
        except Exception as e:
            logger.error(f"Error en vectorización Angular: {str(e)}")
            batch.fail_processing(str(e))
            return batch
    
    def _extract_angular_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extrae metadatos del contenido Angular"""
        metadata = {}
        file_name = Path(file_path).name
        file_ext = Path(file_path).suffix.lower()
        
        # Determinar tipo de archivo
        file_type = 'unknown'
        for ext, pattern in self.angular_file_patterns.items():
            if re.search(pattern, file_name):
                file_type = ext
                break
        
        # Extraer información específica del tipo
        if file_type in self.angular_content_patterns:
            patterns = self.angular_content_patterns[file_type]
            for key, pattern in patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    metadata[key] = matches
        
        # Información general
        metadata['line_count'] = len(content.split('\n'))
        metadata['char_count'] = len(content)
        metadata['file_type'] = file_type
        metadata['file_name'] = file_name
        metadata['file_extension'] = file_ext
        
        return metadata
    
    def _create_vectorization_text(self, file_path: str, content: str, metadata: Dict[str, Any]) -> str:
        """Crea texto optimizado para vectorización"""
        text_parts = []
        
        # Nombre del archivo
        text_parts.append(f"Archivo: {metadata['file_name']}")
        
        # Tipo de archivo
        text_parts.append(f"Tipo: {metadata['file_type'].upper()}")
        
        # Contenido del archivo (limitado para evitar tokens excesivos)
        lines = content.split('\n')[:2000]
        content_preview = '\n'.join(lines)
        text_parts.append(f"Contenido:\n{content_preview}")
        
        # Metadatos extraídos
        for key, value in metadata.items():
            if key not in ['line_count', 'char_count', 'file_type', 'file_name', 'file_extension']:
                text_parts.append(f"{key}: {value}")
        
        return '\n\n'.join(text_parts)

class SpringBootVectorizationService(RepositoryVectorizationService):
    """Servicio especializado para vectorizar repositorios Spring Boot"""
    
    def __init__(self, vector_store_service: VectorStoreServiceImpl, llm_service: LLMServiceImpl):
        super().__init__(vector_store_service, llm_service)
        
        # Patrones para detectar archivos Spring Boot
        self.spring_file_patterns = {
            'java': r'\.(java|JAVA)$',
            'xml': r'\.(xml|XML)$',
            'properties': r'\.(properties|PROPERTIES|yml|YML|yaml|YAML)$',
            'sql': r'\.(sql|SQL)$',
            'json': r'\.(json|JSON)$'
        }
        
        # Patrones para extraer información de archivos Spring Boot
        self.spring_content_patterns = {
            'java': {
                'class_name': r'class\s+(\w+)',
                'interface_name': r'interface\s+(\w+)',
                'method_name': r'(public|private|protected)?\s*(static\s+)?(\w+)\s+(\w+)\s*\(',
                'annotations': r'@(\w+)',
                'package_name': r'package\s+([^;]+)',
                'spring_annotations': r'@(Controller|Service|Repository|Component|Configuration|Bean)',
                'dependencies': r'@Autowired|@Value|@Qualifier'
            },
            'xml': {
                'beans': r'<bean[^>]*>',
                'dependencies': r'<dependency[^>]*>',
                'spring_config': r'<context:component-scan|@EnableAutoConfiguration'
            }
        }
    
    def discover_files(self, repo_path: str) -> List[str]:
        """Descubre archivos Spring Boot en el directorio"""
        spring_files = []
        root_path = Path(repo_path)
        
        logger.info(f"Buscando archivos Spring Boot en: {root_path}")
        
        if not root_path.exists():
            logger.warning(f"El directorio de búsqueda no existe: {root_path}")
            return []
        
        # Buscar archivos Spring Boot recursivamente
        for file_path in root_path.rglob('*'):
            if file_path.is_file():
                # Excluir directorios no relevantes
                if any(part in ['.git', 'target', 'build', '.mvn'] for part in file_path.parts):
                    continue
                    
                for file_type, pattern in self.spring_file_patterns.items():
                    if re.search(pattern, file_path.name):
                        spring_files.append(str(file_path))
                        logger.debug(f"Archivo Spring Boot encontrado: {file_path.name} (tipo: {file_type})")
                        break
        
        logger.info(f"Total de archivos Spring Boot encontrados: {len(spring_files)}")
        return spring_files
    
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """Procesa un archivo Spring Boot individual"""
        try:
            # Leer contenido del archivo
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Extraer metadatos
            metadata = self._extract_spring_metadata(file_path, content)
            
            # Vectorizar contenido
            vectorization_text = self._create_vectorization_text(file_path, content, metadata)
            embedding = await self.llm_service.get_embedding(vectorization_text)
            
            return {
                'success': True,
                'metadata': metadata,
                'embedding': embedding,
                'content_preview': content[:1000]  # Primeros 1000 caracteres
            }
            
        except Exception as e:
            logger.error(f"Error procesando archivo Spring Boot {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def vectorize_repository(self, repo_path: str, batch: VectorizationBatch) -> VectorizationBatch:
        """Vectoriza un repositorio Spring Boot completo"""
        try:
            # Descubrir archivos
            spring_files = self.discover_files(repo_path)
            
            if not spring_files:
                logger.warning("No se encontraron archivos Spring Boot para vectorizar")
                batch.fail_processing("No se encontraron archivos Spring Boot")
                return batch
            
            # Añadir archivos al lote
            for file_path in spring_files:
                file_id = str(hash(file_path))
                batch.add_file(file_id)
            
            # Procesar archivos
            batch.start_processing()
            logger.info(f"Iniciando procesamiento de {len(spring_files)} archivos Spring Boot")
            
            for i, file_path in enumerate(spring_files):
                try:
                    logger.info(f"Procesando archivo {i+1}/{len(spring_files)}: {file_path}")
                    
                    result = await self.process_file(file_path)
                    file_id = str(hash(file_path))
                    
                    if result['success']:
                        batch.mark_file_processed(file_id, success=True)
                        logger.info(f"Archivo {Path(file_path).name} procesado exitosamente")
                    else:
                        batch.mark_file_processed(file_id, success=False)
                        logger.error(f"Error procesando {Path(file_path).name}: {result['error']}")
                        
                except Exception as e:
                    logger.error(f"Error procesando archivo {file_path}: {str(e)}")
                    file_id = str(hash(file_path))
                    batch.mark_file_processed(file_id, success=False)
            
            # Completar lote
            if batch.failed_files > 0:
                logger.warning(f"Fallaron {batch.failed_files} archivos, marcando lote como fallido")
                batch.fail_processing(f"Fallaron {batch.failed_files} archivos")
            else:
                logger.info("Todos los archivos procesados exitosamente")
                batch.complete_processing()
            
            return batch
            
        except Exception as e:
            logger.error(f"Error en vectorización Spring Boot: {str(e)}")
            batch.fail_processing(str(e))
            return batch
    
    def _extract_spring_metadata(self, file_path: str, content: str) -> Dict[str, Any]:
        """Extrae metadatos del contenido Spring Boot"""
        metadata = {}
        file_name = Path(file_path).name
        file_ext = Path(file_path).suffix.lower()
        
        # Determinar tipo de archivo
        file_type = 'unknown'
        for ext, pattern in self.spring_file_patterns.items():
            if re.search(pattern, file_name):
                file_type = ext
                break
        
        # Extraer información específica del tipo
        if file_type in self.spring_content_patterns:
            patterns = self.spring_content_patterns[file_type]
            for key, pattern in patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    metadata[key] = matches
        
        # Información general
        metadata['line_count'] = len(content.split('\n'))
        metadata['char_count'] = len(content)
        metadata['file_type'] = file_type
        metadata['file_name'] = file_name
        metadata['file_extension'] = file_ext
        
        return metadata
    
    def _create_vectorization_text(self, file_path: str, content: str, metadata: Dict[str, Any]) -> str:
        """Crea texto optimizado para vectorización"""
        text_parts = []
        
        # Nombre del archivo
        text_parts.append(f"Archivo: {metadata['file_name']}")
        
        # Tipo de archivo
        text_parts.append(f"Tipo: {metadata['file_type'].upper()}")
        
        # Contenido del archivo (limitado para evitar tokens excesivos)
        lines = content.split('\n')[:2000]
        content_preview = '\n'.join(lines)
        text_parts.append(f"Contenido:\n{content_preview}")
        
        # Metadatos extraídos
        for key, value in metadata.items():
            if key not in ['line_count', 'char_count', 'file_type', 'file_name', 'file_extension']:
                text_parts.append(f"{key}: {value}")
        
        return '\n\n'.join(text_parts)

class RepositoryTechnologyDetector:
    """Detector de tecnología de repositorio"""
    
    @staticmethod
    def detect_technology(repo_path: str) -> str:
        """
        Detecta la tecnología del repositorio basándose en archivos característicos
        
        Returns:
            str: 'nsdk', 'angular', 'spring-boot', o 'unknown'
        """
        root_path = Path(repo_path)
        
        if not root_path.exists():
            return 'unknown'
        
        # Buscar archivos característicos de cada tecnología
        nsdk_indicators = ['*.scr', '*.ncl', '*.inc', '*.prg']
        angular_indicators = ['package.json', 'angular.json', 'tsconfig.json', '*.ts', '*.component.ts']
        spring_indicators = ['pom.xml', 'build.gradle', '*.java', 'application.properties', 'application.yml']
        
        # Contar indicadores de cada tecnología
        nsdk_count = sum(len(list(root_path.rglob(pattern))) for pattern in nsdk_indicators)
        angular_count = sum(len(list(root_path.rglob(pattern))) for pattern in angular_indicators)
        spring_count = sum(len(list(root_path.rglob(pattern))) for pattern in spring_indicators)
        
        logger.info(f"Indicadores encontrados - NSDK: {nsdk_count}, Angular: {angular_count}, Spring Boot: {spring_count}")
        
        # Determinar tecnología dominante
        if nsdk_count > 0 and nsdk_count >= max(angular_count, spring_count):
            return 'nsdk'
        elif angular_count > 0 and angular_count >= max(nsdk_count, spring_count):
            return 'angular'
        elif spring_count > 0 and spring_count >= max(nsdk_count, angular_count):
            return 'spring-boot'
        else:
            return 'unknown'

class UnifiedVectorizationService:
    """Servicio unificado que detecta la tecnología y delega en el servicio especializado apropiado"""
    
    def __init__(self, vector_store_service: VectorStoreServiceImpl, llm_service: LLMServiceImpl, 
                 repository_manager: RepositoryManagerService):
        self.vector_store_service = vector_store_service
        self.llm_service = llm_service
        self.repository_manager = repository_manager
        
        # Almacenamiento en memoria para lotes (temporal)
        self._batches: Dict[str, VectorizationBatch] = {}
        
        # Inicializar servicios especializados
        self.nsdk_service = NSDKVectorizationService(vector_store_service, llm_service)
        self.angular_service = AngularVectorizationService(vector_store_service, llm_service)
        self.spring_service = SpringBootVectorizationService(vector_store_service, llm_service)
        
        # Detector de tecnología
        self.technology_detector = RepositoryTechnologyDetector()
    
    async def vectorize_repository(self, config_id: UUID, repo_type: str, 
                                  branch: str = 'main', force_update: bool = True) -> VectorizationBatch:
        """
        Vectoriza un repositorio detectando automáticamente su tecnología
        
        Args:
            config_id: ID de la configuración
            repo_type: Tipo de repositorio ('source', 'frontend', 'backend')
            branch: Rama del repositorio
            force_update: Si es True, fuerza pull del repositorio y limpia vectorización existente
            
        Returns:
            VectorizationBatch: Lote de vectorización procesado
        """
        logger.info(f"=== INICIANDO VECTORIZACIÓN DE REPOSITORIO ===")
        logger.info(f"Config ID: {config_id}")
        logger.info(f"Repo Type: {repo_type}")
        logger.info(f"Branch: {branch}")
        logger.info(f"Force Update: {force_update}")
        
        try:
            # Crear lote de vectorización
            logger.info("1. Creando lote de vectorización...")
            batch = VectorizationBatch(
                name=f"Vectorización de {repo_type}",
                batch_type=VectorizationBatchType.REPOSITORY,
                config_id=config_id,
                repo_type=repo_type,
                source_repo_branch=branch
            )
            logger.info(f"[OK] Lote creado con ID: {batch.id}")
            logger.info(f"[OK] Lote config_id: {batch.config_id}")
            logger.info(f"[OK] Lote repo_type: {batch.repo_type}")
            
            # Verificar estado del lote antes de procesar
            logger.info(f"Estado del lote antes de procesar: {batch.status}")
            logger.info(f"Total archivos del lote: {batch.total_files}")
            
            # Obtener configuración de la base de datos
            # TODO: Implementar acceso al repositorio de configuraciones
            # Por ahora, simulamos que obtenemos la configuración
            logger.info(f"2. Vectorizando repositorio {repo_type} de configuración {config_id}")
            
            # Si force_update es True, limpiar vectorización existente de esta configuración ANTES de almacenar el batch
            if force_update:
                logger.info("3. Force update activado, limpiando vectorización existente ANTES de almacenar el batch...")
                logger.info(f"Lotes en memoria ANTES de limpiar: {len(self._batches)}")
                logger.info(f"IDs de lotes en memoria: {list(self._batches.keys())}")
                
                await self._clear_existing_vectorization(config_id, repo_type)
                logger.info("[OK] Vectorización existente limpiada")
                
                # Verificar estado después de limpiar
                logger.info(f"Lotes en memoria DESPUÉS de limpiar: {len(self._batches)}")
                logger.info(f"IDs de lotes en memoria: {list(self._batches.keys())}")
            
            # Almacenar el lote en memoria DESPUÉS de limpiar
            logger.info("4. Almacenando lote en memoria DESPUÉS de limpiar...")
            self._batches[batch.id] = batch
            logger.info(f"[OK] Lote {batch.id} almacenado en memoria DESPUÉS de limpiar")
            
            # Verificar que el lote está realmente almacenado
            stored_batch = self._batches.get(batch.id)
            if stored_batch:
                logger.info(f"[OK] Verificación: Lote {batch.id} encontrado en memoria")
                logger.info(f"[OK] Verificación: Lote config_id: {stored_batch.config_id}")
                logger.info(f"[OK] Verificación: Lote repo_type: {stored_batch.repo_type}")
            else:
                logger.error(f"[ERROR] Lote {batch.id} NO encontrado en memoria después de almacenar")
                raise Exception(f"Lote {batch.id} no se almacenó correctamente")
            
            # TODO: Obtener URL del repositorio desde la configuración
            # Por ahora, simulamos que tenemos la URL
            repo_url = f"https://example.com/{repo_type}-repo"
            repo_name = f"{repo_type}_repo"
            
            # Clonar o actualizar repositorio permanentemente (con pull forzado si force_update)
            logger.info(f"5. Clonando/actualizando repositorio: {repo_url} (branch: {branch}, force_update: {force_update})")
            repo_path = self.repository_manager.clone_repository(
                repo_url, repo_name, branch, None, None, force_update
            )
            logger.info(f"[OK] Repositorio disponible en: {repo_path}")
            
            # Detectar tecnología del repositorio
            logger.info("6. Detectando tecnología del repositorio...")
            technology = self.technology_detector.detect_technology(str(repo_path))
            logger.info(f"[OK] Tecnología detectada: {technology}")
            
            # Delegar en el servicio especializado apropiado
            logger.info("7. Delegando en servicio especializado...")
            if technology == 'nsdk':
                logger.info("[OK] Usando servicio NSDK para vectorización")
                await self.nsdk_service.vectorize_repository(str(repo_path), batch)
            elif technology == 'angular':
                logger.info("[OK] Usando servicio Angular para vectorización")
                await self.angular_service.vectorize_repository(str(repo_path), batch)
            elif technology == 'spring-boot':
                logger.info("[OK] Usando servicio Spring Boot para vectorización")
                await self.spring_service.vectorize_repository(str(repo_path), batch)
            else:
                logger.warning(f"⚠️ Tecnología no reconocida: {technology}. Intentando vectorización genérica...")
                # Intentar vectorización genérica o fallar
                batch.fail_processing(f"Tecnología no reconocida: {technology}")
            
            # El lote ya está almacenado, solo actualizar el estado final
            logger.info(f"[OK] Lote {batch.id} procesado completamente")
            logger.info(f"Estado final del lote: {batch.status}")
            logger.info(f"Total archivos procesados: {batch.total_files}")
            
            # Verificación final
            final_stored_batch = self._batches.get(batch.id)
            if final_stored_batch:
                logger.info(f"[OK] Verificación final: Lote {batch.id} disponible para el frontend")
            else:
                logger.error(f"[ERROR] Lote {batch.id} NO disponible para el frontend")
            
            return batch
            
        except Exception as e:
            logger.error(f"❌ ERROR en vectorización del repositorio: {str(e)}")
            logger.error(f"❌ Traceback completo: {e}")
            
            if 'batch' in locals():
                logger.info(f"[OK] Lote ya creado, marcando como fallido: {batch.id}")
                batch.fail_processing(str(e))
                # Almacenar el lote fallido
                self._batches[batch.id] = batch
                logger.info(f"[OK] Lote fallido {batch.id} almacenado en memoria")
                return batch
            else:
                logger.info("⚠️ Lote no creado, creando lote fallido...")
                # Crear lote fallido
                batch = VectorizationBatch(
                    name=f"Vectorización fallida de {repo_type}",
                    batch_type=VectorizationBatchType.REPOSITORY,
                    config_id=config_id,
                    repo_type=repo_type,
                    source_repo_branch=branch
                )
                batch.fail_processing(str(e))
                # Almacenar el lote fallido
                self._batches[batch.id] = batch
                logger.info(f"[OK] Lote fallido {batch.id} creado y almacenado en memoria")
                return batch
    
    async def vectorize_module(self, config_id: UUID, repo_type: str, module_path: str, 
                               branch: str = 'main') -> VectorizationBatch:
        """
        Vectoriza un módulo específico de un repositorio
        
        Args:
            config_id: ID de la configuración
            repo_type: Tipo de repositorio ('source', 'frontend', 'backend')
            module_path: Ruta del módulo a vectorizar
            branch: Rama del repositorio
            
        Returns:
            VectorizationBatch: Lote de vectorización del módulo
        """
        try:
            # Crear lote de vectorización
            batch = VectorizationBatch(
                name=f"Vectorización del módulo {module_path}",
                batch_type=VectorizationBatchType.MODULE,
                config_id=config_id,
                repo_type=repo_type,
                source_repo_branch=branch
            )
            
            # Obtener configuración de la base de datos
            # TODO: Implementar acceso al repositorio de configuraciones
            # Por ahora, simulamos que obtenemos la configuración
            logger.info(f"Vectorizando módulo {module_path} del repositorio {repo_type} de configuración {config_id}")
            
            # Almacenar el lote en memoria DESPUÉS de procesar
            self._batches[batch.id] = batch
            logger.info(f"Lote de módulo {batch.id} almacenado en memoria DESPUÉS de procesar")
            
            # TODO: Obtener URL del repositorio desde la configuración
            # Por ahora, simulamos que tenemos la URL
            repo_url = f"https://example.com/{repo_type}-repo"
            repo_name = f"{repo_type}_repo"
            
            # Clonar o actualizar repositorio
            logger.info(f"Clonando/actualizando repositorio: {repo_url} (branch: {branch})")
            repo_path = self.repository_manager.clone_repository(
                repo_url, repo_name, branch, None, None, False
            )
            logger.info(f"Repositorio disponible en: {repo_path}")
            
            # Verificar que el módulo existe
            module_full_path = Path(repo_path) / module_path
            if not module_full_path.exists():
                error_msg = f"Módulo {module_path} no encontrado en el repositorio"
                logger.error(error_msg)
                batch.fail_processing(error_msg)
                return batch
            
            # Detectar tecnología del repositorio
            technology = self.technology_detector.detect_technology(str(repo_path))
            logger.info(f"Tecnología detectada: {technology}")
            
            # Delegar en el servicio especializado apropiado
            if technology == 'nsdk':
                logger.info("Usando servicio NSDK para vectorización del módulo")
                await self.nsdk_service.vectorize_module(str(repo_path), module_path, batch)
            elif technology == 'angular':
                logger.info("Usando servicio Angular para vectorización del módulo")
                await self.angular_service.vectorize_module(str(repo_path), module_path, batch)
            elif technology == 'spring-boot':
                logger.info("Usando servicio Spring Boot para vectorización del módulo")
                await self.spring_service.vectorize_module(str(repo_path), module_path, batch)
            else:
                logger.warning(f"Tecnología no reconocida: {technology}. Intentando vectorización genérica...")
                # Intentar vectorización genérica o fallar
                batch.fail_processing(f"Tecnología no reconocida: {technology}")
            
            # El lote ya está almacenado, solo actualizar el estado final
            logger.info(f"Lote de módulo {batch.id} procesado completamente")
            
            return batch
            
        except Exception as e:
            logger.error(f"Error en vectorización del módulo: {str(e)}")
            if 'batch' in locals():
                batch.fail_processing(str(e))
                # Almacenar el lote fallido
                self._batches[batch.id] = batch
                return batch
            else:
                # Crear lote fallido
                batch = VectorizationBatch(
                    name=f"Vectorización fallida del módulo {module_path}",
                    batch_type=VectorizationBatchType.MODULE,
                    config_id=config_id,
                    repo_type=repo_type,
                    source_repo_branch=branch
                )
                batch.fail_processing(str(e))
                # Almacenar el lote fallido
                self._batches[batch.id] = batch
                return batch
    
    async def _clear_existing_vectorization(self, config_id: UUID = None, repo_type: str = None):
        """
        Limpia la vectorización existente
        
        Args:
            config_id: ID de la configuración específica
            repo_type: Tipo de repositorio ('source', 'frontend', 'backend')
        """
        logger.info(f"=== INICIANDO LIMPIEZA DE VECTORIZACIÓN ===")
        logger.info(f"Config ID: {config_id}")
        logger.info(f"Repo Type: {repo_type}")
        logger.info(f"Lotes en memoria ANTES de limpiar: {len(self._batches)}")
        logger.info(f"IDs de lotes en memoria: {list(self._batches.keys())}")
        
        try:
            if config_id and repo_type:
                logger.info(f"1. Limpiando vectorización de configuración {config_id}, repositorio {repo_type}")
            else:
                logger.info("1. Limpiando TODA la vectorización existente...")
            
            # Limpiar vector store
            logger.info("2. Limpiando vector store...")
            if hasattr(self, 'vector_store_service') and self.vector_store_service:
                # Obtener configuración del vector store (asumiendo que está disponible)
                # Por ahora, usar configuración por defecto
                config = {
                    'type': 'faiss',  # Por defecto FAISS
                    'collectionName': 'nsdk-embeddings'
                }
                
                if config_id and repo_type:
                    # TODO: Implementar limpieza selectiva en el vector store
                    logger.info("⚠️ Limpieza selectiva del vector store no implementada aún")
                else:
                    # Limpiar toda la colección
                    logger.info("Limpiando toda la colección del vector store...")
                    success = self.vector_store_service.clear_collection(config)
                    if success:
                        logger.info("[OK] Vector store completamente limpiado")
                    else:
                        logger.warning("[WARNING] No se pudo limpiar el vector store completamente")
            else:
                logger.warning("[WARNING] Vector store service no disponible")
            
            # Limpiar lotes en memoria
            logger.info("3. Limpiando lotes en memoria...")
            if config_id and repo_type:
                # Limpiar solo los lotes de esta configuración y tipo
                logger.info(f"Buscando lotes con config_id={config_id} y repo_type={repo_type}")
                keys_to_remove = []
                
                for key, batch in self._batches.items():
                    logger.info(f"Evaluando lote {key}: config_id={batch.config_id}, repo_type={batch.repo_type}")
                    if batch.config_id == config_id and batch.repo_type == repo_type:
                        keys_to_remove.append(key)
                        logger.info(f"[OK] Lote {key} marcado para eliminación")
                    else:
                        logger.info(f"[SKIP] Lote {key} NO marcado para eliminación")
                
                logger.info(f"Lotes marcados para eliminación: {keys_to_remove}")
                
                for key in keys_to_remove:
                    logger.info(f"Eliminando lote {key}...")
                    del self._batches[key]
                    logger.info(f"[OK] Lote {key} eliminado")
                
                logger.info(f"[OK] Lotes de configuración {config_id}, tipo {repo_type} limpiados: {len(keys_to_remove)} lotes eliminados")
            else:
                # Limpiar todos los lotes
                logger.info("Limpiando TODOS los lotes...")
                self._batches.clear()
                logger.info("[OK] Todos los lotes en memoria limpiados")
            
            # Verificación final
            logger.info(f"Lotes en memoria DESPUÉS de limpiar: {len(self._batches)}")
            logger.info(f"IDs de lotes en memoria: {list(self._batches.keys())}")
            
            if config_id and repo_type:
                logger.info(f"[OK] Vectorización de configuración {config_id}, tipo {repo_type} limpiada")
            else:
                logger.info("[OK] Toda la vectorización existente limpiada completamente")
            
        except Exception as e:
            logger.error(f"❌ Error limpiando vectorización existente: {str(e)}")
            # No fallar la operación principal por errores de limpieza
    
    async def clear_all_vectorization(self):
        """Limpia TODA la vectorización existente (para 'vectorizar todos')"""
        try:
            logger.info("Limpieza completa de toda la vectorización solicitada...")
            await self._clear_existing_vectorization()  # Sin config_id ni repo_type = limpiar todo
            logger.info("Limpieza completa de vectorización finalizada")
            return True
        except Exception as e:
            logger.error(f"Error en limpieza completa: {str(e)}")
            return False

    async def search_similar_code(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Busca código similar usando el vector store"""
        try:
            # Obtener embedding de la consulta
            query_embedding = await self.llm_service.get_embedding(query)
            
            if not query_embedding:
                raise Exception("No se pudo obtener embedding de la consulta")
            
            # Buscar en el vector store
            results = self.vector_store_service.search_similar(
                query_embedding, 
                limit=limit
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda de código similar: {str(e)}")
            return []
    
    def get_batch_by_id(self, batch_id: str) -> Optional[VectorizationBatch]:
        """
        Obtiene un lote de vectorización por su ID
        
        Args:
            batch_id: ID del lote
            
        Returns:
            Optional[VectorizationBatch]: El lote o None si no existe
        """
        logger.info(f"=== BUSCANDO LOTE POR ID ===")
        logger.info(f"Batch ID solicitado: {batch_id}")
        logger.info(f"Total lotes en memoria: {len(self._batches)}")
        logger.info(f"IDs de lotes disponibles: {list(self._batches.keys())}")
        
        # Buscar el lote
                                                                                                                                                                                batch = self._batches.get(batch_id)
        
        if batch:
            logger.info(f"[OK] Lote {batch_id} ENCONTRADO")
            logger.info(f"[OK] Lote config_id: {batch.config_id}")
            logger.info(f"[OK] Lote repo_type: {batch.repo_type}")
            logger.info(f"[OK] Lote status: {batch.status}")
            logger.info(f"[OK] Lote total_files: {batch.total_files}")
        else:
            logger.error(f"[ERROR] Lote {batch_id} NO ENCONTRADO")
            logger.error(f"[ERROR] Lotes disponibles: {list(self._batches.keys())}")
            
            # Verificar si hay algún lote con config_id o repo_type similar
            for key, available_batch in self._batches.items():
                logger.info(f"Lote disponible {key}: config_id={available_batch.config_id}, repo_type={available_batch.repo_type}")
        
        return batch
    
    def get_vectorization_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de vectorización separadas por tipo de repositorio"""
        try:
            # Estadísticas agregadas
            total_files = 0
            vectorized_files = 0
            pending_files = 0
            error_files = 0
            last_vectorization = None
            
            # Estadísticas por tipo de repositorio
            nsdk_stats = {'total': 0, 'vectorized': 0, 'pending': 0, 'error': 0}
            angular_stats = {'total': 0, 'vectorized': 0, 'pending': 0, 'error': 0}
            spring_stats = {'total': 0, 'vectorized': 0, 'pending': 0, 'error': 0}
            
            # Calcular estadísticas desde los lotes almacenados
            for batch in self._batches.values():
                total_files += batch.total_files
                
                if batch.status == VectorizationBatchStatus.COMPLETED:
                    vectorized_files += batch.successful_files
                    error_files += batch.failed_files
                elif batch.status == VectorizationBatchStatus.IN_PROGRESS:
                    pending_files += batch.total_files - batch.processed_files
                elif batch.status == VectorizationBatchStatus.FAILED:
                    error_files += batch.total_files
                
                # Encontrar la última vectorización
                if batch.completed_at and (last_vectorization is None or batch.completed_at > last_vectorization):
                    last_vectorization = batch.completed_at
                
                # Categorizar por tipo de repositorio usando la tecnología detectada
                # Primero intentar detectar la tecnología del repositorio actual
                repo_path = None
                try:
                    # Obtener el nombre del repositorio del tipo
                    repo_name = f"{batch.repo_type}_repo"
                    # Construir la ruta del repositorio clonado
                    repo_path = Path(self.repository_manager.get_repo_path(repo_name))
                except Exception as e:
                    logger.warning(f"No se pudo obtener ruta del repositorio {batch.repo_type}: {e}")
                
                # Detectar tecnología del repositorio
                technology = 'unknown'
                if repo_path and repo_path.exists():
                    technology = self.technology_detector.detect_technology(str(repo_path))
                    logger.info(f"Tecnología detectada para {batch.repo_type}: {technology}")
                else:
                    # Fallback: intentar categorizar por tipo de repositorio
                    if batch.repo_type == 'source':
                        technology = 'nsdk'
                    elif batch.repo_type == 'frontend':
                        technology = 'angular'
                    elif batch.repo_type == 'backend':
                        technology = 'spring-boot'
                    logger.info(f"Tecnología inferida por tipo para {batch.repo_type}: {technology}")
                
                # Categorizar estadísticas según la tecnología detectada
                if technology == 'nsdk':
                    if batch.status == VectorizationBatchStatus.COMPLETED:
                        nsdk_stats['vectorized'] += batch.successful_files
                        nsdk_stats['error'] += batch.failed_files
                    elif batch.status == VectorizationBatchStatus.IN_PROGRESS:
                        nsdk_stats['pending'] += batch.total_files - batch.processed_files
                    elif batch.status == VectorizationBatchStatus.FAILED:
                        nsdk_stats['error'] += batch.total_files
                    nsdk_stats['total'] += batch.total_files
                    logger.info(f"Estadísticas NSDK actualizadas: {nsdk_stats}")
                elif technology == 'angular':
                    if batch.status == VectorizationBatchStatus.COMPLETED:
                        angular_stats['vectorized'] += batch.successful_files
                        angular_stats['error'] += batch.failed_files
                    elif batch.status == VectorizationBatchStatus.IN_PROGRESS:
                        angular_stats['pending'] += batch.total_files - batch.processed_files
                    elif batch.status == VectorizationBatchStatus.FAILED:
                        angular_stats['error'] += batch.total_files
                    angular_stats['total'] += batch.total_files
                    logger.info(f"Estadísticas Angular actualizadas: {angular_stats}")
                elif technology == 'spring-boot':
                    if batch.status == VectorizationBatchStatus.COMPLETED:
                        spring_stats['vectorized'] += batch.successful_files
                        spring_stats['error'] += batch.failed_files
                    elif batch.status == VectorizationBatchStatus.IN_PROGRESS:
                        spring_stats['pending'] += batch.total_files - batch.processed_files
                    elif batch.status == VectorizationBatchStatus.FAILED:
                        spring_stats['error'] += batch.total_files
                    spring_stats['total'] += batch.total_files
                    logger.info(f"Estadísticas Spring Boot actualizadas: {spring_stats}")
                else:
                    logger.warning(f"Tecnología no reconocida '{technology}' para {batch.repo_type}, no se categorizan estadísticas")
            
            logger.info(f"Estadísticas finales - NSDK: {nsdk_stats}, Angular: {angular_stats}, Spring Boot: {spring_stats}")
            
            return {
                'total_files': total_files,
                'vectorized_files': vectorized_files,
                'pending_files': pending_files,
                'error_files': error_files,
                'last_vectorization': last_vectorization.isoformat() if last_vectorization else None,
                'by_repository_type': {
                    'nsdk': nsdk_stats,
                    'angular': angular_stats,
                    'spring_boot': spring_stats
                }
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                'total_files': 0,
                'vectorized_files': 0,
                'pending_files': 0,
                'error_files': 0,
                'last_vectorization': None,
                'by_repository_type': {
                    'nsdk': {'total': 0, 'vectorized': 0, 'pending': 0, 'error': 0},
                    'angular': {'total': 0, 'vectorized': 0, 'pending': 0, 'error': 0},
                    'spring_boot': {'total': 0, 'vectorized': 0, 'pending': 0, 'error': 0}
                }
            }
