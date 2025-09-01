from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import uuid
from datetime import datetime
from ...domain.entities.nsdk_file_analysis import NSDKFileAnalysis, NSDKFileAnalysisModel
import logging

logger = logging.getLogger(__name__)

class NSDKFileAnalysisRepository:
    """Repositorio para manejar análisis de archivos NSDK"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, analysis: NSDKFileAnalysis) -> NSDKFileAnalysis:
        """Crea un nuevo análisis de archivo NSDK"""
        try:
            # Generar ID si no existe
            if not analysis.id:
                analysis.id = str(uuid.uuid4())
            
            # Crear modelo
            model = NSDKFileAnalysisModel(
                id=analysis.id,
                file_path=analysis.file_path,
                file_name=analysis.file_name,
                file_type=analysis.file_type,
                repository_name=analysis.repository_name,
                line_count=analysis.line_count,
                char_count=analysis.char_count,
                size_kb=analysis.size_kb,
                function_count=analysis.function_count,
                functions=analysis.functions,
                field_count=analysis.field_count,
                fields=analysis.fields,
                button_count=analysis.button_count,
                buttons=analysis.buttons,
                module_name=analysis.module_name,
                screen_name=analysis.screen_name,
                analysis_status=analysis.analysis_status,
                analysis_date=analysis.analysis_date or datetime.utcnow(),
                file_metadata=analysis.file_metadata or {},
                created_at=analysis.created_at or datetime.utcnow(),
                updated_at=analysis.updated_at or datetime.utcnow()
            )
            
            self.db.add(model)
            self.db.commit()
            self.db.refresh(model)
            
            logger.info(f"Análisis de archivo NSDK creado: {analysis.file_path}")
            return self._model_to_entity(model)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando análisis de archivo NSDK: {str(e)}")
            raise
    
    def get_by_id(self, analysis_id: str) -> Optional[NSDKFileAnalysis]:
        """Obtiene un análisis por ID"""
        try:
            model = self.db.query(NSDKFileAnalysisModel).filter(
                NSDKFileAnalysisModel.id == analysis_id
            ).first()
            
            return self._model_to_entity(model) if model else None
            
        except Exception as e:
            logger.error(f"Error obteniendo análisis por ID {analysis_id}: {str(e)}")
            return None
    
    def get_by_file_path(self, file_path: str, repository_name: str) -> Optional[NSDKFileAnalysis]:
        """Obtiene un análisis por ruta de archivo y repositorio"""
        try:
            logger.info(f"Buscando archivo en BD - Path: {file_path}, Repo: {repository_name}")
            model = self.db.query(NSDKFileAnalysisModel).filter(
                and_(
                    NSDKFileAnalysisModel.file_path == file_path,
                    NSDKFileAnalysisModel.repository_name == repository_name
                )
            ).first()
            
            result = self._model_to_entity(model) if model else None
            logger.info(f"Resultado de búsqueda: {'encontrado' if result else 'no encontrado'}")
            return result
            
        except Exception as e:
            logger.error(f"Error obteniendo análisis por ruta {file_path}: {str(e)}")
            return None
    
    def get_by_repository(self, repository_name: str) -> List[NSDKFileAnalysis]:
        """Obtiene todos los análisis de un repositorio"""
        try:
            models = self.db.query(NSDKFileAnalysisModel).filter(
                NSDKFileAnalysisModel.repository_name == repository_name
            ).all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error obteniendo análisis del repositorio {repository_name}: {str(e)}")
            return []
    
    def get_files_by_directory_id(self, directory_id: str) -> List[NSDKFileAnalysis]:
        """Obtiene archivos que pertenecen a un directorio específico"""
        try:
            # Por ahora, usamos la ruta del directorio para filtrar
            # En el futuro, podríamos agregar un campo directory_id a la entidad
            models = self.db.query(NSDKFileAnalysisModel).filter(
                NSDKFileAnalysisModel.file_path.like(f"%{directory_id}%")
            ).all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos del directorio {directory_id}: {str(e)}")
            return []
    
    def get_files_by_directory_ids(self, directory_ids: List[str]) -> List[NSDKFileAnalysis]:
        """Obtiene archivos que pertenecen a múltiples directorios"""
        try:
            all_files = []
            for directory_id in directory_ids:
                files = self.get_files_by_directory_id(directory_id)
                all_files.extend(files)
            
            return all_files
            
        except Exception as e:
            logger.error(f"Error obteniendo archivos de múltiples directorios: {str(e)}")
            return []
    
    def get_by_type(self, file_type: str, repository_name: str) -> List[NSDKFileAnalysis]:
        """Obtiene análisis por tipo de archivo"""
        try:
            models = self.db.query(NSDKFileAnalysisModel).filter(
                and_(
                    NSDKFileAnalysisModel.file_type == file_type,
                    NSDKFileAnalysisModel.repository_name == repository_name
                )
            ).all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error obteniendo análisis por tipo {file_type}: {str(e)}")
            return []
    
    def get_by_status(self, status: str, repository_name: str) -> List[NSDKFileAnalysis]:
        """Obtiene análisis por estado"""
        try:
            models = self.db.query(NSDKFileAnalysisModel).filter(
                and_(
                    NSDKFileAnalysisModel.analysis_status == status,
                    NSDKFileAnalysisModel.repository_name == repository_name
                )
            ).all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error obteniendo análisis por estado {status}: {str(e)}")
            return []
    
    def get_by_type_and_status(self, file_type: str, status: str, repository_name: str) -> List[NSDKFileAnalysis]:
        """Obtiene análisis por tipo de archivo y estado"""
        try:
            models = self.db.query(NSDKFileAnalysisModel).filter(
                and_(
                    NSDKFileAnalysisModel.file_type == file_type,
                    NSDKFileAnalysisModel.analysis_status == status,
                    NSDKFileAnalysisModel.repository_name == repository_name
                )
            ).all()
            
            return [self._model_to_entity(model) for model in models]
            
        except Exception as e:
            logger.error(f"Error obteniendo análisis por tipo {file_type} y estado {status}: {str(e)}")
            return []
    
    def update(self, analysis: NSDKFileAnalysis) -> Optional[NSDKFileAnalysis]:
        """Actualiza un análisis existente"""
        try:
            model = self.db.query(NSDKFileAnalysisModel).filter(
                NSDKFileAnalysisModel.id == analysis.id
            ).first()
            
            if not model:
                logger.warning(f"Análisis no encontrado para actualizar: {analysis.id}")
                return None
            
            # Actualizar campos
            model.file_path = analysis.file_path
            model.file_name = analysis.file_name
            model.file_type = analysis.file_type
            model.repository_name = analysis.repository_name
            model.line_count = analysis.line_count
            model.char_count = analysis.char_count
            model.size_kb = analysis.size_kb
            model.function_count = analysis.function_count
            model.functions = analysis.functions
            model.field_count = analysis.field_count
            model.fields = analysis.fields
            model.button_count = analysis.button_count
            model.buttons = analysis.buttons
            model.module_name = analysis.module_name
            model.screen_name = analysis.screen_name
            model.analysis_status = analysis.analysis_status
            model.analysis_date = analysis.analysis_date
            model.file_metadata = analysis.file_metadata
            model.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(model)
            
            logger.info(f"Análisis de archivo NSDK actualizado: {analysis.file_path}")
            return self._model_to_entity(model)
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error actualizando análisis de archivo NSDK: {str(e)}")
            raise
    
    def delete(self, analysis_id: str) -> bool:
        """Elimina un análisis por ID"""
        try:
            model = self.db.query(NSDKFileAnalysisModel).filter(
                NSDKFileAnalysisModel.id == analysis_id
            ).first()
            
            if not model:
                logger.warning(f"Análisis no encontrado para eliminar: {analysis_id}")
                return False
            
            self.db.delete(model)
            self.db.commit()
            
            logger.info(f"Análisis de archivo NSDK eliminado: {analysis_id}")
            return True
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error eliminando análisis de archivo NSDK: {str(e)}")
            return False
    
    def bulk_create(self, analyses: List[NSDKFileAnalysis]) -> List[NSDKFileAnalysis]:
        """Crea múltiples análisis en lote"""
        try:
            created_analyses = []
            
            for analysis in analyses:
                # Generar ID si no existe
                if not analysis.id:
                    analysis.id = str(uuid.uuid4())
                
                # Crear modelo
                model = NSDKFileAnalysisModel(
                    id=analysis.id,
                    file_path=analysis.file_path,
                    file_name=analysis.file_name,
                    file_type=analysis.file_type,
                    repository_name=analysis.repository_name,
                    line_count=analysis.line_count,
                    char_count=analysis.char_count,
                    size_kb=analysis.size_kb,
                    function_count=analysis.function_count,
                    functions=analysis.functions,
                    field_count=analysis.field_count,
                    fields=analysis.fields,
                    button_count=analysis.button_count,
                    buttons=analysis.buttons,
                    module_name=analysis.module_name,
                    screen_name=analysis.screen_name,
                    analysis_status=analysis.analysis_status,
                    analysis_date=analysis.analysis_date or datetime.utcnow(),
                    file_metadata=analysis.file_metadata or {},
                    created_at=analysis.created_at or datetime.utcnow(),
                    updated_at=analysis.updated_at or datetime.utcnow()
                )
                
                self.db.add(model)
                created_analyses.append(analysis)
            
            self.db.commit()
            logger.info(f"Creados {len(created_analyses)} análisis de archivos NSDK en lote")
            return created_analyses
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error creando análisis en lote: {str(e)}")
            raise
    
    def get_statistics(self, repository_name: str) -> Dict[str, Any]:
        """Obtiene estadísticas del repositorio"""
        try:
            total_files = self.db.query(NSDKFileAnalysisModel).filter(
                NSDKFileAnalysisModel.repository_name == repository_name
            ).count()
            
            analyzed_files = self.db.query(NSDKFileAnalysisModel).filter(
                and_(
                    NSDKFileAnalysisModel.repository_name == repository_name,
                    NSDKFileAnalysisModel.analysis_status == 'analyzed'
                )
            ).count()
            
            pending_files = self.db.query(NSDKFileAnalysisModel).filter(
                and_(
                    NSDKFileAnalysisModel.repository_name == repository_name,
                    NSDKFileAnalysisModel.analysis_status == 'pending'
                )
            ).count()
            
            error_files = self.db.query(NSDKFileAnalysisModel).filter(
                and_(
                    NSDKFileAnalysisModel.repository_name == repository_name,
                    NSDKFileAnalysisModel.analysis_status == 'error'
                )
            ).count()
            
            # Estadísticas por tipo
            type_stats = {}
            for file_type in ['module', 'screen', 'include', 'program']:
                count = self.db.query(NSDKFileAnalysisModel).filter(
                    and_(
                        NSDKFileAnalysisModel.repository_name == repository_name,
                        NSDKFileAnalysisModel.file_type == file_type
                    )
                ).count()
                type_stats[file_type] = count
            
            return {
                'total_files': total_files,
                'analyzed_files': analyzed_files,
                'pending_files': pending_files,
                'error_files': error_files,
                'type_distribution': type_stats,
                'analysis_progress': (analyzed_files / total_files * 100) if total_files > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas del repositorio {repository_name}: {str(e)}")
            return {}
    
    def _model_to_entity(self, model: NSDKFileAnalysisModel) -> NSDKFileAnalysis:
        """Convierte un modelo SQLAlchemy a entidad de dominio"""
        return NSDKFileAnalysis(
            id=model.id,
            file_path=model.file_path,
            file_name=model.file_name,
            file_type=model.file_type,
            repository_name=model.repository_name,
            line_count=model.line_count,
            char_count=model.char_count,
            size_kb=model.size_kb,
            function_count=model.function_count,
            functions=model.functions or [],
            field_count=model.field_count,
            fields=model.fields or [],
            button_count=model.button_count,
            buttons=model.buttons or [],
            module_name=model.module_name,
            screen_name=model.screen_name,
            analysis_status=model.analysis_status,
            analysis_date=model.analysis_date,
            file_metadata=model.file_metadata or {},
            created_at=model.created_at,
            updated_at=model.updated_at
        )
