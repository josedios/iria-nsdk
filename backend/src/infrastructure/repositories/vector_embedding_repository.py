from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import logging
from ...domain.entities.vector_embedding import VectorEmbedding
import hashlib

logger = logging.getLogger(__name__)

class VectorEmbeddingRepository:
    """Repositorio para operaciones de embeddings vectorizados"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, vector_embedding: VectorEmbedding) -> VectorEmbedding:
        """Crea un nuevo embedding vectorizado"""
        try:
            logger.info(f"Guardando embedding para archivo: {vector_embedding.file_path}")
            self.db.add(vector_embedding)
            self.db.commit()
            self.db.refresh(vector_embedding)
            logger.info(f"Embedding guardado exitosamente: {vector_embedding.id}")
            return vector_embedding
        except Exception as e:
            logger.error(f"Error guardando embedding: {str(e)}")
            self.db.rollback()
            raise
    
    def get_by_file_path(self, file_path: str, config_id: str) -> Optional[VectorEmbedding]:
        """Obtiene un embedding por ruta de archivo y configuración"""
        try:
            return self.db.query(VectorEmbedding).filter(
                and_(
                    VectorEmbedding.file_path == file_path,
                    VectorEmbedding.config_id == config_id
                )
            ).first()
        except Exception as e:
            logger.error(f"Error obteniendo embedding por file_path: {str(e)}")
            return None
    
    def get_by_content_hash(self, content_hash: str, config_id: str) -> Optional[VectorEmbedding]:
        """Obtiene un embedding por hash del contenido y configuración"""
        try:
            return self.db.query(VectorEmbedding).filter(
                and_(
                    VectorEmbedding.content_hash == content_hash,
                    VectorEmbedding.config_id == config_id
                )
            ).first()
        except Exception as e:
            logger.error(f"Error obteniendo embedding por content_hash: {str(e)}")
            return None
    
    def get_by_config_and_repo(self, config_id: str, repo_type: str, branch: str = 'main') -> List[VectorEmbedding]:
        """Obtiene todos los embeddings de una configuración y repositorio"""
        try:
            return self.db.query(VectorEmbedding).filter(
                and_(
                    VectorEmbedding.config_id == config_id,
                    VectorEmbedding.repo_type == repo_type,
                    VectorEmbedding.repo_branch == branch
                )
            ).all()
        except Exception as e:
            logger.error(f"Error obteniendo embeddings por config y repo: {str(e)}")
            return []
    
    def update(self, vector_embedding: VectorEmbedding) -> VectorEmbedding:
        """Actualiza un embedding existente"""
        try:
            logger.info(f"Actualizando embedding: {vector_embedding.id}")
            self.db.commit()
            self.db.refresh(vector_embedding)
            logger.info(f"Embedding actualizado exitosamente: {vector_embedding.id}")
            return vector_embedding
        except Exception as e:
            logger.error(f"Error actualizando embedding: {str(e)}")
            self.db.rollback()
            raise
    
    def delete_by_config(self, config_id: str) -> bool:
        """Elimina todos los embeddings de una configuración"""
        try:
            logger.info(f"Eliminando embeddings para config_id: {config_id}")
            count = self.db.query(VectorEmbedding).filter(
                VectorEmbedding.config_id == config_id
            ).delete()
            self.db.commit()
            logger.info(f"Eliminados {count} embeddings para config_id: {config_id}")
            return True
        except Exception as e:
            logger.error(f"Error eliminando embeddings: {str(e)}")
            self.db.rollback()
            return False
    
    def delete_by_config_and_repo(self, config_id: str, repo_type: str, branch: str = 'main') -> bool:
        """Elimina embeddings de una configuración y repositorio específicos"""
        try:
            logger.info(f"Eliminando embeddings para config_id: {config_id}, repo_type: {repo_type}, branch: {branch}")
            count = self.db.query(VectorEmbedding).filter(
                and_(
                    VectorEmbedding.config_id == config_id,
                    VectorEmbedding.repo_type == repo_type,
                    VectorEmbedding.repo_branch == branch
                )
            ).delete()
            self.db.commit()
            logger.info(f"Eliminados {count} embeddings")
            return True
        except Exception as e:
            logger.error(f"Error eliminando embeddings: {str(e)}")
            self.db.rollback()
            return False
    
    def get_all(self) -> List[VectorEmbedding]:
        """Obtiene todos los embeddings"""
        try:
            return self.db.query(VectorEmbedding).all()
        except Exception as e:
            logger.error(f"Error obteniendo todos los embeddings: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de embeddings"""
        try:
            total = self.db.query(VectorEmbedding).count()
            
            # Estadísticas por tipo de archivo
            file_types = self.db.query(VectorEmbedding.file_type).distinct().all()
            file_type_stats = {}
            for file_type in file_types:
                count = self.db.query(VectorEmbedding).filter(
                    VectorEmbedding.file_type == file_type[0]
                ).count()
                file_type_stats[file_type[0]] = count
            
            # Estadísticas por configuración
            configs = self.db.query(VectorEmbedding.config_id).distinct().all()
            config_stats = {}
            for config_id in configs:
                count = self.db.query(VectorEmbedding).filter(
                    VectorEmbedding.config_id == config_id[0]
                ).count()
                config_stats[config_id[0]] = count
            
            return {
                'total_embeddings': total,
                'file_types': file_type_stats,
                'configurations': config_stats
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas: {str(e)}")
            return {}
    
    @staticmethod
    def calculate_content_hash(content: str) -> str:
        """Calcula el hash del contenido del archivo"""
        return hashlib.md5(content.encode('utf-8')).hexdigest()
