import os
import re
import tempfile
import shutil
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from git import Repo, GitCommandError

from ...domain.entities.nsdk_file import NSDKFile, NSDKFileType, NSDKFileStatus
from ...domain.entities.vectorization_batch import VectorizationBatch, VectorizationBatchStatus, VectorizationBatchType
from .vector_store_service_impl import VectorStoreServiceImpl
from .llm_service_impl import LLMServiceImpl

logger = logging.getLogger(__name__)

class NSDKVectorizationService:
    """Servicio para vectorizar archivos NSDK (.SCR, .NCL, .INC, .PRG)"""
    
    def __init__(self, vector_store_service: VectorStoreServiceImpl, llm_service: LLMServiceImpl):
        self.vector_store_service = vector_store_service
        self.llm_service = llm_service
        
        # Almacenamiento en memoria para lotes (temporal)
        self._batches: Dict[str, VectorizationBatch] = {}
        
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
    
    async def vectorize_repository(self, repo_url: str, branch: str = 'main', 
                           username: Optional[str] = None, token: Optional[str] = None) -> VectorizationBatch:
        """
        Vectoriza un repositorio completo de NSDK
        
        Args:
            repo_url: URL del repositorio
            branch: Rama a procesar
            username: Usuario para autenticación
            token: Token para autenticación
            
        Returns:
            VectorizationBatch: Lote de vectorización creado
        """
        try:
            # Crear lote de vectorización
            batch = VectorizationBatch(
                name=f"Vectorización de {repo_url.split('/')[-1]}",
                batch_type=VectorizationBatchType.REPOSITORY,
                source_repo_url=repo_url,
                source_repo_branch=branch
            )
            
            # Clonar repositorio
            temp_dir = self._clone_repository(repo_url, branch, username, token)
            
            try:
                # Encontrar archivos NSDK
                nsdk_files = self._discover_nsdk_files(temp_dir)
                logger.info(f"Encontrados {len(nsdk_files)} archivos NSDK")
                
                # Añadir archivos al lote
                for file_path in nsdk_files:
                    file_id = str(hash(file_path))
                    batch.add_file(file_id)
                
                # Procesar archivos
                batch.start_processing()
                self._process_files_batch(nsdk_files, batch)
                
                if batch.failed_files:
                    batch.fail_processing(f"Fallaron {len(batch.failed_files)} archivos")
                else:
                    batch.complete_processing()
                    
            finally:
                # Limpiar directorio temporal
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            # Almacenar el lote en memoria
            self._batches[batch.id] = batch
            return batch
            
        except Exception as e:
            logger.error(f"Error en vectorización del repositorio: {str(e)}")
            if 'batch' in locals():
                batch.fail_processing(str(e))
                # Almacenar el lote fallido
                self._batches[batch.id] = batch
                return batch
            else:
                # Crear lote fallido
                batch = VectorizationBatch(
                    name=f"Vectorización fallida de {repo_url.split('/')[-1]}",
                    batch_type=VectorizationBatchType.REPOSITORY,
                    source_repo_url=repo_url,
                    source_repo_branch=branch
                )
                batch.fail_processing(str(e))
                # Almacenar el lote fallido
                self._batches[batch.id] = batch
                return batch
    
    async def vectorize_module(self, module_path: str, repo_url: str, branch: str = 'main') -> VectorizationBatch:
        """
        Vectoriza un módulo específico
        
        Args:
            module_path: Ruta del módulo
            repo_url: URL del repositorio
            branch: Rama a procesar
            
        Returns:
            VectorizationBatch: Lote de vectorización
        """
        try:
            batch = VectorizationBatch(
                name=f"Vectorización del módulo {module_path}",
                batch_type=VectorizationBatchType.MODULE,
                source_repo_url=repo_url,
                source_repo_branch=branch
            )
            
            temp_dir = self._clone_repository(repo_url, branch)
            
            try:
                module_files = self._discover_nsdk_files(temp_dir, module_path)
                for file_path in module_files:
                    file_id = str(hash(file_path))
                    batch.add_file(file_id)
                
                batch.start_processing()
                self._process_files_batch(module_files, batch)
                
                if batch.failed_files:
                    batch.fail_processing(f"Fallaron {len(batch.failed_files)} archivos")
                else:
                    batch.complete_processing()
                    
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
            
            return batch
            
        except Exception as e:
            logger.error(f"Error en vectorización del módulo: {str(e)}")
            batch = VectorizationBatch(
                name=f"Vectorización fallida del módulo {module_path}",
                batch_type=VectorizationBatchType.MODULE,
                source_repo_url=repo_url,
                source_repo_branch=branch
            )
            batch.fail_processing(str(e))
            return batch
    
    def _clone_repository(self, repo_url: str, branch: str, 
                         username: Optional[str] = None, token: Optional[str] = None) -> str:
        """Clona un repositorio a un directorio temporal"""
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Si hay credenciales, usar autenticación en el comando git
            if username and token:
                # Construir URL con autenticación
                if '://' in repo_url:
                    proto, rest = repo_url.split('://', 1)
                    # Asegurar que no haya caracteres especiales en username/token
                    safe_username = username.replace(':', '%3A').replace('@', '%40')
                    safe_token = token.replace(':', '%3A').replace('@', '%40')
                    auth_url = f"{proto}://{safe_username}:{safe_token}@{rest}"
                else:
                    auth_url = repo_url
                
                logger.info(f"Clonando repositorio con autenticación: {auth_url}")
                Repo.clone_from(auth_url, temp_dir, branch=branch, depth=1)
            else:
                # Clonar sin autenticación
                logger.info(f"Clonando repositorio público: {repo_url}")
                Repo.clone_from(repo_url, temp_dir, branch=branch, depth=1)
            
            logger.info(f"Repositorio clonado exitosamente en {temp_dir}")
            return temp_dir
            
        except GitCommandError as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f"Error de Git al clonar: {str(e)}")
            raise Exception(f"Error al clonar repositorio: {str(e)}")
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            logger.error(f"Error inesperado al clonar: {str(e)}")
            raise Exception(f"Error inesperado al clonar repositorio: {str(e)}")
    
    def _discover_nsdk_files(self, root_dir: str, module_path: Optional[str] = None) -> List[str]:
        """Descubre archivos NSDK en el directorio"""
        nsdk_files = []
        root_path = Path(root_dir)
        
        # Si se especifica un módulo, buscar solo en esa ruta
        if module_path:
            search_path = root_path / module_path
        else:
            search_path = root_path
        
        if not search_path.exists():
            return []
        
        # Buscar archivos NSDK recursivamente
        for file_path in search_path.rglob('*'):
            if file_path.is_file():
                for file_type, pattern in self.nsdk_file_patterns.items():
                    if re.search(pattern, file_path.name):
                        nsdk_files.append(str(file_path))
                        break
        
        return nsdk_files
    
    async def _process_files_batch(self, file_paths: List[str], batch: VectorizationBatch):
        """Procesa un lote de archivos NSDK"""
        for file_path in file_paths:
            try:
                file_id = str(hash(file_path))
                
                # Crear entidad NSDKFile
                nsdk_file = self._create_nsdk_file(file_path)
                
                # Procesar contenido
                self._process_nsdk_file(nsdk_file)
                
                # Vectorizar
                await self._vectorize_nsdk_file(nsdk_file)
                
                # Marcar como procesado exitosamente
                batch.mark_file_processed(file_id, success=True)
                
            except Exception as e:
                logger.error(f"Error procesando archivo {file_path}: {str(e)}")
                file_id = str(hash(file_path))
                batch.mark_file_processed(file_id, success=False)
    
    def _create_nsdk_file(self, file_path: str) -> NSDKFile:
        """Crea una entidad NSDKFile a partir de la ruta del archivo"""
        path_obj = Path(file_path)
        file_name = path_obj.name
        
        # Determinar tipo de archivo
        file_type = NSDKFileType.UNKNOWN
        for ext, pattern in self.nsdk_file_patterns.items():
            if re.search(pattern, file_name):
                file_type = NSDKFileType(ext)
                break
        
        # Determinar module_id basado en la estructura de directorios
        module_id = None
        if len(path_obj.parts) > 1:
            # Asumir que el primer directorio después de la raíz es el módulo
            module_id = path_obj.parts[-2] if len(path_obj.parts) > 2 else path_obj.parts[-1]
        
        return NSDKFile(
            name=file_name,
            file_path=file_path,
            file_type=file_type,
            module_id=module_id
        )
    
    def _process_nsdk_file(self, nsdk_file: NSDKFile):
        """Procesa el contenido de un archivo NSDK"""
        try:
            # Leer contenido del archivo
            with open(nsdk_file.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Establecer contenido
            nsdk_file.set_content(content)
            
            # Extraer metadatos
            metadata = self._extract_nsdk_metadata(content, nsdk_file.file_type)
            nsdk_file.metadata = metadata
            
            logger.info(f"Archivo {nsdk_file.name} procesado exitosamente")
            
        except Exception as e:
            logger.error(f"Error procesando contenido de {nsdk_file.name}: {str(e)}")
            nsdk_file.update_status(NSDKFileStatus.ERROR, str(e))
            raise
    
    def _extract_nsdk_metadata(self, content: str, file_type: NSDKFileType) -> Dict[str, Any]:
        """Extrae metadatos del contenido NSDK"""
        metadata = {}
        
        if file_type == NSDKFileType.SCR:
            # Extraer información de pantallas
            patterns = self.nsdk_content_patterns['scr']
            for key, pattern in patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    metadata[key] = matches
        
        elif file_type == NSDKFileType.NCL:
            # Extraer información de módulos
            patterns = self.nsdk_content_patterns['ncl']
            for key, pattern in patterns.items():
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    metadata[key] = matches
        
        # Información general
        metadata['line_count'] = len(content.split('\n'))
        metadata['char_count'] = len(content)
        metadata['file_type'] = file_type.value
        
        return metadata
    
    async def _vectorize_nsdk_file(self, nsdk_file: NSDKFile):
        """Vectoriza un archivo NSDK usando el servicio de embeddings"""
        try:
            # Crear texto para vectorización
            vectorization_text = self._create_vectorization_text(nsdk_file)
            
            # Obtener embedding del LLM
            embedding = await self.llm_service.get_embedding(vectorization_text)
            
            if embedding:
                nsdk_file.set_vector_embedding(embedding)
                logger.info(f"Archivo {nsdk_file.name} vectorizado exitosamente")
            else:
                raise Exception("No se pudo obtener embedding del LLM")
                
        except Exception as e:
            logger.error(f"Error vectorizando {nsdk_file.name}: {str(e)}")
            nsdk_file.update_status(NSDKFileStatus.ERROR, str(e))
            raise
    
    def _create_vectorization_text(self, nsdk_file: NSDKFile) -> str:
        """Crea texto optimizado para vectorización"""
        text_parts = []
        
        # Nombre del archivo
        text_parts.append(f"Archivo: {nsdk_file.name}")
        
        # Tipo de archivo
        text_parts.append(f"Tipo: {nsdk_file.file_type.value.upper()}")
        
        # Módulo
        if nsdk_file.module_id:
            text_parts.append(f"Módulo: {nsdk_file.module_id}")
        
        # Contenido del archivo (limitado para evitar tokens excesivos)
        if nsdk_file.content:
            # Limitar a las primeras 2000 líneas para evitar tokens excesivos
            lines = nsdk_file.content.split('\n')[:2000]
            content_preview = '\n'.join(lines)
            text_parts.append(f"Contenido:\n{content_preview}")
        
        # Metadatos extraídos
        if nsdk_file.metadata:
            for key, value in nsdk_file.metadata.items():
                if key not in ['line_count', 'char_count', 'file_type']:
                    text_parts.append(f"{key}: {value}")
        
        return '\n\n'.join(text_parts)
    
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
    
    def get_vectorization_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de vectorización"""
        # TODO: Implementar estadísticas desde la base de datos
        return {
            'total_files': 0,
            'vectorized_files': 0,
            'pending_files': 0,
            'error_files': 0,
            'last_vectorization': None
        }
    
    def get_batch_by_id(self, batch_id: str) -> Optional[VectorizationBatch]:
        """
        Obtiene un lote de vectorización por su ID
        
        Args:
            batch_id: ID del lote
            
        Returns:
            Optional[VectorizationBatch]: El lote o None si no existe
        """
        return self._batches.get(batch_id)
