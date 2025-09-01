from typing import List, Optional
from sqlalchemy.orm import Session
from ...domain.entities.ai_analysis_result import AIAnalysisResult
import logging

logger = logging.getLogger(__name__)

class AIAnalysisRepository:
    """Repositorio para gestionar resultados de análisis IA"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, analysis_result: AIAnalysisResult) -> AIAnalysisResult:
        """Crea un nuevo resultado de análisis"""
        try:
            logger.info(f"Guardando análisis IA en BD: file_analysis_id={analysis_result.file_analysis_id}")
            self.db.add(analysis_result)
            self.db.commit()
            self.db.refresh(analysis_result)
            logger.info(f"Resultado de análisis IA creado exitosamente: {analysis_result.id}")
            return analysis_result
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando resultado de análisis IA: {str(e)}")
            raise
    
    def get_by_id(self, analysis_id: str) -> Optional[AIAnalysisResult]:
        """Obtiene un resultado de análisis por ID"""
        try:
            return self.db.query(AIAnalysisResult).filter(
                AIAnalysisResult.id == analysis_id
            ).first()
        except Exception as e:
            logger.error(f"Error obteniendo resultado de análisis IA {analysis_id}: {str(e)}")
            return None
    
    def get_by_file_analysis_id(self, file_analysis_id: str) -> Optional[AIAnalysisResult]:
        """Obtiene el resultado de análisis más reciente para un fichero"""
        try:
            logger.info(f"Buscando análisis IA en BD para file_analysis_id: {file_analysis_id}")
            
            # Primero verificar si hay algún análisis para este file_id
            count = self.db.query(AIAnalysisResult).filter(
                AIAnalysisResult.file_analysis_id == file_analysis_id
            ).count()
            logger.info(f"Total de análisis encontrados para {file_analysis_id}: {count}")
            
            if count == 0:
                logger.warning(f"No hay análisis en BD para file_analysis_id: {file_analysis_id}")
                return None
            
            # Obtener el más reciente
            result = self.db.query(AIAnalysisResult).filter(
                AIAnalysisResult.file_analysis_id == file_analysis_id
            ).order_by(AIAnalysisResult.created_at.desc()).first()
            
            if result:
                logger.info(f"Análisis más reciente encontrado: {result.id} creado en {result.created_at}")
            else:
                logger.warning(f"No se pudo obtener el análisis más reciente para {file_analysis_id}")
            
            return result
        except Exception as e:
            logger.error(f"Error obteniendo resultado de análisis para fichero {file_analysis_id}: {str(e)}")
            return None
    
    def get_all_by_file_analysis_id(self, file_analysis_id: str) -> List[AIAnalysisResult]:
        """Obtiene todos los resultados de análisis para un fichero (historial)"""
        try:
            return self.db.query(AIAnalysisResult).filter(
                AIAnalysisResult.file_analysis_id == file_analysis_id
            ).order_by(AIAnalysisResult.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error obteniendo historial de análisis para fichero {file_analysis_id}: {str(e)}")
            return []
    
    def update(self, analysis_result: AIAnalysisResult) -> AIAnalysisResult:
        """Actualiza un resultado de análisis"""
        try:
            self.db.commit()
            self.db.refresh(analysis_result)
            logger.info(f"Resultado de análisis IA actualizado: {analysis_result.id}")
            return analysis_result
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando resultado de análisis IA: {str(e)}")
            raise
    
    def delete(self, analysis_id: str) -> bool:
        """Elimina un resultado de análisis"""
        try:
            analysis_result = self.get_by_id(analysis_id)
            if analysis_result:
                self.db.delete(analysis_result)
                self.db.commit()
                logger.info(f"Resultado de análisis IA eliminado: {analysis_id}")
                return True
            return False
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error eliminando resultado de análisis IA {analysis_id}: {str(e)}")
            return False
    
    def get_by_complexity(self, complexity: str) -> List[AIAnalysisResult]:
        """Obtiene resultados de análisis por complejidad"""
        try:
            return self.db.query(AIAnalysisResult).filter(
                AIAnalysisResult.complexity == complexity
            ).order_by(AIAnalysisResult.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error obteniendo análisis por complejidad {complexity}: {str(e)}")
            return []
    
    def get_all(self) -> List[AIAnalysisResult]:
        """Obtiene todos los resultados de análisis"""
        try:
            return self.db.query(AIAnalysisResult).order_by(AIAnalysisResult.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error obteniendo todos los análisis: {str(e)}")
            return []
    
    def get_statistics(self) -> dict:
        """Obtiene estadísticas de los análisis realizados"""
        try:
            total = self.db.query(AIAnalysisResult).count()
            by_complexity = self.db.query(
                AIAnalysisResult.complexity,
                self.db.func.count(AIAnalysisResult.id)
            ).group_by(AIAnalysisResult.complexity).all()
            
            by_file_type = self.db.query(
                AIAnalysisResult.file_type,
                self.db.func.count(AIAnalysisResult.id)
            ).group_by(AIAnalysisResult.file_type).all()
            
            return {
                'total_analyses': total,
                'by_complexity': dict(by_complexity),
                'by_file_type': dict(by_file_type)
            }
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de análisis: {str(e)}")
            return {
                'total_analyses': 0,
                'by_complexity': {},
                'by_file_type': {}
            }
