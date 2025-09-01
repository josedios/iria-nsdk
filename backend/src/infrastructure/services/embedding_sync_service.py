import logging
from typing import List, Dict, Any, Optional
from ...domain.entities.vector_embedding import VectorEmbedding
from ...infrastructure.repositories.vector_embedding_repository import VectorEmbeddingRepository
from .vector_store_service_impl import VectorStoreServiceImpl

logger = logging.getLogger(__name__)

class EmbeddingSyncService:
    """Servicio para sincronizar embeddings entre BD y Vector Store"""
    
    def __init__(self, vector_store_service: VectorStoreServiceImpl):
        self.vector_store_service = vector_store_service
    
    async def sync_embeddings_to_vector_store(self, vector_embedding_repo: VectorEmbeddingRepository, 
                                            config_id: str = None) -> bool:
        """Sincroniza embeddings desde BD al Vector Store"""
        try:
            logger.info("Iniciando sincronización de embeddings a Vector Store...")
            logger.info(f"Config ID: {config_id}")
            logger.info(f"Vector store service: {self.vector_store_service}")
            
            # Obtener embeddings de la BD
            if config_id:
                embeddings = vector_embedding_repo.get_by_config_and_repo(config_id, 'source', 'main')
                logger.info(f"Obtenidos {len(embeddings)} embeddings para config_id: {config_id}")
            else:
                embeddings = vector_embedding_repo.get_all()
                logger.info(f"Obtenidos {len(embeddings)} embeddings totales")
            
            if not embeddings:
                logger.warning("No hay embeddings para sincronizar")
                return True
            
            # Detectar la dimensión de los embeddings
            if embeddings:
                detected_dimension = len(embeddings[0].embedding)
                logger.info(f"Dimensión detectada en embeddings: {detected_dimension}")
            else:
                detected_dimension = 1536  # Dimensión por defecto
                logger.info(f"Usando dimensión por defecto: {detected_dimension}")
            
            # Configuración para FAISS con dimensión detectada
            config = {
                'type': 'faiss',
                'collectionName': 'nsdk-embeddings',
                'dimension': detected_dimension
            }
            
            # Inicializar colección si no existe
            logger.info(f"Inicializando colección con config: {config}")
            init_result = self.vector_store_service.initialize_collection(config)
            logger.info(f"Resultado de inicialización: {init_result}")
            if not init_result:
                logger.error("No se pudo inicializar la colección del Vector Store")
                return False
            
            # Preparar datos para el Vector Store
            embedding_vectors = []
            metadata_list = []
            ids_list = []
            
            for embedding in embeddings:
                embedding_vectors.append(embedding.embedding)
                metadata_list.append({
                    'file_path': embedding.file_path,
                    'file_name': embedding.file_name,
                    'file_type': embedding.file_type,
                    'content_hash': embedding.content_hash,
                    'config_id': embedding.config_id,
                    'repo_type': embedding.repo_type,
                    'repo_branch': embedding.repo_branch,
                    'created_at': embedding.created_at.isoformat() if embedding.created_at else None,
                    'file_metadata': embedding.file_metadata or {}
                })
                ids_list.append(embedding.id)
            
            # Añadir embeddings al Vector Store
            success = self.vector_store_service.add_embeddings(
                config=config,
                embeddings=embedding_vectors,
                metadata=metadata_list,
                ids=ids_list
            )
            
            if success:
                logger.info(f"Sincronización completada: {len(embeddings)} embeddings cargados al Vector Store")
                return True
            else:
                logger.error("Error en la sincronización de embeddings")
                return False
                
        except Exception as e:
            logger.error(f"Error en sincronización de embeddings: {str(e)}")
            return False
    
    async def load_embeddings_from_db(self, vector_embedding_repo: VectorEmbeddingRepository) -> bool:
        """Carga embeddings desde BD al Vector Store al iniciar el sistema"""
        try:
            logger.info("Cargando embeddings desde BD al Vector Store...")
            return await self.sync_embeddings_to_vector_store(vector_embedding_repo)
        except Exception as e:
            logger.error(f"Error cargando embeddings desde BD: {str(e)}")
            return False
    
    def get_vector_store_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del Vector Store"""
        try:
            config = {
                'type': 'faiss',
                'collectionName': 'nsdk-embeddings'
            }
            
            # Verificar si FAISS está inicializado
            if hasattr(self.vector_store_service, 'faiss_index') and self.vector_store_service.faiss_index:
                total_vectors = self.vector_store_service.faiss_index.ntotal
                dimension = self.vector_store_service.faiss_index.d
                return {
                    'vector_store_type': 'faiss',
                    'total_vectors': total_vectors,
                    'dimension': dimension,
                    'is_initialized': True
                }
            else:
                return {
                    'vector_store_type': 'faiss',
                    'total_vectors': 0,
                    'dimension': 0,
                    'is_initialized': False
                }
                
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del Vector Store: {str(e)}")
            return {
                'vector_store_type': 'faiss',
                'total_vectors': 0,
                'dimension': 0,
                'is_initialized': False,
                'error': str(e)
            }
