from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
from datetime import datetime
from ...domain.entities.nsdk_file_analysis import NSDKFileAnalysis
from ...infrastructure.repositories.nsdk_file_analysis_repository import NSDKFileAnalysisRepository
from .repository_manager_service import RepositoryManagerService

logger = logging.getLogger(__name__)

class NSDKAnalysisSyncService:
    """Servicio para sincronizar análisis de archivos NSDK con la base de datos"""
    
    def __init__(self, repository_manager: RepositoryManagerService, analysis_repository: NSDKFileAnalysisRepository):
        self.repository_manager = repository_manager
        self.analysis_repository = analysis_repository
    
    def sync_repository_analysis(self, repository_name: str, force_resync: bool = False) -> Dict[str, Any]:
        """
        Sincroniza el análisis de archivos NSDK de un repositorio con la base de datos
        
        Args:
            repository_name: Nombre del repositorio
            force_resync: Si es True, reanaliza todos los archivos
            
        Returns:
            Diccionario con estadísticas de la sincronización
        """
        try:
            logger.info(f"Iniciando sincronización de análisis para repositorio: {repository_name}")
            
            # Verificar que el repositorio existe
            if not self.repository_manager.is_repository_cloned(repository_name):
                raise Exception(f"Repositorio {repository_name} no está clonado")
            
            # Obtener estructura del repositorio
            repo_tree = self.repository_manager.get_repository_tree(repository_name)
            if not repo_tree:
                raise Exception(f"No se pudo obtener la estructura del repositorio {repository_name}")
            
            # Extraer archivos NSDK del árbol
            nsdk_files = self._extract_nsdk_files_from_tree(repo_tree, repository_name)
            logger.info(f"Encontrados {len(nsdk_files)} archivos NSDK en {repository_name}")
            
            # Sincronizar con la base de datos
            sync_stats = self._sync_files_with_database(nsdk_files, repository_name, force_resync)
            
            logger.info(f"Sincronización completada para {repository_name}: {sync_stats}")
            return sync_stats
            
        except Exception as e:
            logger.error(f"Error en sincronización de análisis para {repository_name}: {str(e)}")
            raise
    
    def _extract_nsdk_files_from_tree(self, tree_node: Dict[str, Any], repository_name: str) -> List[NSDKFileAnalysis]:
        """Extrae archivos NSDK del árbol del repositorio"""
        nsdk_files = []
        
        def traverse_tree(node: Dict[str, Any], current_path: str = ""):
            if node.get('is_file') and node.get('type') in ['module', 'screen', 'include', 'program']:
                # Crear entidad de análisis
                analysis = NSDKFileAnalysis(
                    file_path=node.get('path', ''),
                    file_name=node.get('name', ''),
                    file_type=node.get('type', ''),
                    repository_name=repository_name,
                    line_count=node.get('line_count', 0),
                    char_count=node.get('char_count', 0),
                    size_kb=node.get('size_kb', 0),
                    function_count=node.get('function_count', 0),
                    functions=node.get('functions', []),
                    field_count=node.get('field_count', 0),
                    fields=node.get('fields', []),
                    button_count=node.get('button_count', 0),
                    buttons=node.get('buttons', []),
                    module_name=node.get('module_name'),
                    screen_name=node.get('screen_name'),
                    analysis_status='analyzed' if node.get('line_count') else 'pending',
                    analysis_date=datetime.utcnow() if node.get('line_count') else None,
                    file_metadata={
                        'extension': node.get('extension', ''),
                        'depth': node.get('depth', 0),
                        'original_tree_data': {k: v for k, v in node.items() if k not in ['children']}
                    }
                )
                nsdk_files.append(analysis)
            
            # Recorrer hijos
            for child in node.get('children', []):
                traverse_tree(child, current_path)
        
        traverse_tree(tree_node)
        return nsdk_files
    
    def _sync_files_with_database(self, nsdk_files: List[NSDKFileAnalysis], repository_name: str, force_resync: bool) -> Dict[str, Any]:
        """Sincroniza archivos NSDK con la base de datos"""
        try:
            stats = {
                'total_files': len(nsdk_files),
                'created': 0,
                'updated': 0,
                'skipped': 0,
                'errors': 0
            }
            
            for nsdk_file in nsdk_files:
                try:
                    # Verificar si ya existe en la base de datos
                    existing_analysis = self.analysis_repository.get_by_file_path(
                        nsdk_file.file_path, 
                        repository_name
                    )
                    
                    if existing_analysis and not force_resync:
                        # Verificar si necesita actualización
                        if self._needs_update(existing_analysis, nsdk_file):
                            updated_analysis = self.analysis_repository.update(nsdk_file)
                            if updated_analysis:
                                stats['updated'] += 1
                                logger.debug(f"Análisis actualizado: {nsdk_file.file_path}")
                            else:
                                stats['errors'] += 1
                                logger.error(f"Error actualizando análisis: {nsdk_file.file_path}")
                        else:
                            stats['skipped'] += 1
                            logger.debug(f"Análisis sin cambios, saltado: {nsdk_file.file_path}")
                    else:
                        # Crear nuevo análisis
                        if existing_analysis:
                            # Usar el ID existente para la actualización
                            nsdk_file.id = existing_analysis.id
                        
                        created_analysis = self.analysis_repository.create(nsdk_file)
                        if created_analysis:
                            stats['created'] += 1
                            logger.debug(f"Análisis creado: {nsdk_file.file_path}")
                        else:
                            stats['errors'] += 1
                            logger.error(f"Error creando análisis: {nsdk_file.file_path}")
                
                except Exception as e:
                    stats['errors'] += 1
                    logger.error(f"Error procesando archivo {nsdk_file.file_path}: {str(e)}")
                    continue
            
            logger.info(f"Sincronización completada: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error en sincronización con base de datos: {str(e)}")
            raise
    
    def _needs_update(self, existing: NSDKFileAnalysis, new: NSDKFileAnalysis) -> bool:
        """Verifica si un análisis existente necesita actualización"""
        # Comparar campos clave
        fields_to_compare = [
            'line_count', 'char_count', 'size_kb', 'function_count', 
            'field_count', 'button_count', 'functions', 'fields', 'buttons'
        ]
        
        for field in fields_to_compare:
            if getattr(existing, field) != getattr(new, field):
                return True
        
        return False
    
    def get_repository_analysis_status(self, repository_name: str) -> Dict[str, Any]:
        """Obtiene el estado del análisis de un repositorio"""
        try:
            # Obtener estadísticas de la base de datos
            db_stats = self.analysis_repository.get_statistics(repository_name)
            
            # Obtener estadísticas del repositorio en disco
            repo_tree = self.repository_manager.get_repository_tree(repository_name)
            if repo_tree:
                disk_files = self._extract_nsdk_files_from_tree(repo_tree, repository_name)
                disk_stats = {
                    'total_files_on_disk': len(disk_files),
                    'file_types_on_disk': {}
                }
                
                for file in disk_files:
                    file_type = file.file_type
                    if file_type not in disk_stats['file_types_on_disk']:
                        disk_stats['file_types_on_disk'][file_type] = 0
                    disk_stats['file_types_on_disk'][file_type] += 1
            else:
                disk_stats = {'total_files_on_disk': 0, 'file_types_on_disk': {}}
            
            # Combinar estadísticas
            combined_stats = {
                'repository_name': repository_name,
                'database_stats': db_stats,
                'disk_stats': disk_stats,
                'sync_status': 'in_sync' if db_stats.get('total_files', 0) == disk_stats['total_files_on_disk'] else 'out_of_sync',
                'last_sync_check': datetime.utcnow().isoformat()
            }
            
            return combined_stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estado de análisis para {repository_name}: {str(e)}")
            return {
                'repository_name': repository_name,
                'error': str(e),
                'last_sync_check': datetime.utcnow().isoformat()
            }
    
    def cleanup_orphaned_analyses(self, repository_name: str) -> Dict[str, Any]:
        """Limpia análisis huérfanos (archivos que ya no existen en el repositorio)"""
        try:
            logger.info(f"Iniciando limpieza de análisis huérfanos para {repository_name}")
            
            # Obtener todos los análisis de la base de datos
            db_analyses = self.analysis_repository.get_by_repository(repository_name)
            
            # Obtener archivos actuales del repositorio
            repo_tree = self.repository_manager.get_repository_tree(repository_name)
            if not repo_tree:
                raise Exception(f"No se pudo obtener la estructura del repositorio {repository_name}")
            
            current_files = self._extract_nsdk_files_from_tree(repo_tree, repository_name)
            current_file_paths = {f.file_path for f in current_files}
            
            # Encontrar análisis huérfanos
            orphaned_analyses = [
                analysis for analysis in db_analyses 
                if analysis.file_path not in current_file_paths
            ]
            
            # Eliminar análisis huérfanos
            deleted_count = 0
            for orphaned in orphaned_analyses:
                if self.analysis_repository.delete(orphaned.id):
                    deleted_count += 1
                    logger.debug(f"Análisis huérfano eliminado: {orphaned.file_path}")
            
            logger.info(f"Limpieza completada: {deleted_count} análisis huérfanos eliminados")
            return {
                'total_orphaned': len(orphaned_analyses),
                'deleted': deleted_count,
                'errors': len(orphaned_analyses) - deleted_count
            }
            
        except Exception as e:
            logger.error(f"Error en limpieza de análisis huérfanos para {repository_name}: {str(e)}")
            raise
