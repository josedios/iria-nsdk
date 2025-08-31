from typing import List, Dict, Any, Optional
import logging
from uuid import UUID
from ...domain.entities.vectorization_batch import VectorizationBatch
from ...infrastructure.services.nsdk_vectorization_service import UnifiedVectorizationService

logger = logging.getLogger(__name__)

class VectorizationUseCase:
    """Caso de uso para la vectorización de repositorios"""
    
    def __init__(self, unified_vectorization_service: UnifiedVectorizationService):
        self.unified_vectorization_service = unified_vectorization_service
    
    async def vectorize_repository(self, config_id: str, repo_type: str, branch: str = 'main',
                           force_update: bool = True) -> VectorizationBatch:
        """
        Vectoriza un repositorio completo detectando automáticamente su tecnología
        
        Args:
            config_id: ID de la configuración
            repo_type: Tipo de repositorio ('source', 'frontend', 'backend')
            branch: Rama a procesar
            force_update: Si es True, fuerza pull del repositorio y limpia vectorización existente
            
        Returns:
            VectorizationBatch: Lote de vectorización
        """
        try:
            logger.info(f"Iniciando vectorización del repositorio: {repo_type} de configuración {config_id} (force_update: {force_update})")
            
            # Ejecutar vectorización con pull forzado y limpieza
            batch = await self.unified_vectorization_service.vectorize_repository(
                config_id=config_id,
                repo_type=repo_type,
                branch=branch,
                force_update=force_update
            )
            
            logger.info(f"Vectorización completada. Estado: {batch.status.value}")
            return batch
            
        except Exception as e:
            logger.error(f"Error en caso de uso de vectorización: {str(e)}")
            # Crear lote fallido
            batch = VectorizationBatch(
                name=f"Vectorización fallida de {repo_type}",
                config_id=UUID(config_id),
                repo_type=repo_type,
                source_repo_branch=branch
            )
            batch.fail_processing(str(e))
            return batch
    
    async def vectorize_module(self, config_id: str, repo_type: str, module_path: str, branch: str = 'main') -> VectorizationBatch:
        """
        Vectoriza un módulo específico
        
        Args:
            config_id: ID de la configuración
            repo_type: Tipo de repositorio ('source', 'frontend', 'backend')
            module_path: Ruta del módulo
            branch: Rama a procesar
            
        Returns:
            VectorizationBatch: Lote de vectorización
        """
        try:
            logger.info(f"Iniciando vectorización del módulo: {module_path}")
            
            # Ejecutar vectorización del módulo
            batch = await self.unified_vectorization_service.vectorize_module(
                config_id=config_id,
                repo_type=repo_type,
                module_path=module_path,
                branch=branch
            )
            
            logger.info(f"Vectorización del módulo completada. Estado: {batch.status.value}")
            return batch
            
        except Exception as e:
            logger.error(f"Error en vectorización del módulo: {str(e)}")
            # Crear lote fallido
            batch = VectorizationBatch(
                name=f"Vectorización fallida del módulo {module_path}",
                config_id=UUID(config_id),
                repo_type=repo_type,
                source_repo_branch=branch
            )
            batch.fail_processing(str(e))
            return batch
    
    async def search_similar_code(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Busca código similar usando el vector store
        
        Args:
            query: Consulta de búsqueda
            limit: Número máximo de resultados
            
        Returns:
            List[Dict[str, Any]]: Resultados de búsqueda
        """
        try:
            logger.info(f"Buscando código similar para: {query}")
            
            # Ejecutar búsqueda
            results = await self.unified_vectorization_service.search_similar_code(
                query=query,
                limit=limit
            )
            
            logger.info(f"Búsqueda completada. Resultados: {len(results)}")
            return results
            
        except Exception as e:
            logger.error(f"Error en búsqueda de código similar: {str(e)}")
            return []
    
    def get_vectorization_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de vectorización
        
        Returns:
            Dict[str, Any]: Estadísticas de vectorización
        """
        try:
            logger.info("Obteniendo estadísticas de vectorización")
            
            # Obtener estadísticas
            stats = self.unified_vectorization_service.get_vectorization_stats()
            
            logger.info("Estadísticas obtenidas exitosamente")
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {
                'error': str(e),
                'total_files': 0,
                'vectorized_files': 0,
                'pending_files': 0,
                'error_files': 0,
                'last_vectorization': None
            }
    
    def get_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtiene el estado de un lote de vectorización
        
        Args:
            batch_id: ID del lote
            
        Returns:
            Optional[Dict[str, Any]]: Estado del lote o None si no existe
        """
        try:
            logger.info(f"Obteniendo estado del lote: {batch_id}")
            
            # Buscar el lote en el servicio de vectorización
            batch = self.unified_vectorization_service.get_batch_by_id(batch_id)
            
            if batch:
                # Convertir a diccionario para la respuesta
                return {
                    'id': batch.id,
                    'name': batch.name,
                    'batch_type': batch.batch_type.value,
                    'config_id': str(batch.config_id),
                    'repo_type': batch.repo_type,
                    'source_repo_branch': batch.source_repo_branch,
                    'status': batch.status.value,
                    'total_files': batch.total_files,
                    'processed_files': batch.processed_files,
                    'successful_files': batch.successful_files,
                    'failed_files': batch.failed_files,
                    'file_ids': batch.file_ids,
                    'error_files': batch.error_files,
                    'metadata': batch.metadata,
                    'started_at': batch.started_at.isoformat() if batch.started_at else None,
                    'completed_at': batch.completed_at.isoformat() if batch.completed_at else None,
                    'created_at': batch.created_at.isoformat() if batch.created_at else None,
                    'updated_at': batch.updated_at.isoformat() if batch.updated_at else None,
                    'progress_percentage': batch.get_progress_percentage(),
                    'success_rate': batch.get_success_rate(),
                    'duration': batch.get_duration()
                }
            else:
                logger.warning(f"Lote no encontrado: {batch_id}")
                return None
            
        except Exception as e:
            logger.error(f"Error obteniendo estado del lote: {str(e)}")
            return None
    
    def cancel_batch(self, batch_id: str) -> bool:
        """
        Cancela un lote de vectorización en progreso
        
        Args:
            batch_id: ID del lote
            
        Returns:
            bool: True si se canceló exitosamente
        """
        try:
            logger.info(f"Cancelando lote: {batch_id}")
            
            # TODO: Implementar cancelación del lote
            # Por ahora retornamos False
            logger.warning("Cancelación de lote no implementada aún")
            return False
            
        except Exception as e:
            logger.error(f"Error cancelando lote: {str(e)}")
            return False