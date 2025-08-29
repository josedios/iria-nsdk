from typing import List, Dict, Any, Optional
from pathlib import Path
from src.infrastructure.repositories.nsdk_directory_repository import NSDKDirectoryRepository
from src.infrastructure.repositories.nsdk_file_analysis_repository import NSDKFileAnalysisRepository
from src.domain.entities.nsdk_directory import NSDKDirectory
from src.domain.entities.nsdk_file_analysis import NSDKFileAnalysis
import uuid
import logging

logger = logging.getLogger(__name__)

class DirectoryTreeService:
    """Servicio para manejar la estructura jerárquica de directorios y archivos"""
    
    def __init__(self, directory_repo: NSDKDirectoryRepository, file_repo: NSDKFileAnalysisRepository):
        self.directory_repo = directory_repo
        self.file_repo = file_repo
    
    def build_directory_tree_from_path(self, repository_path: str, repository_name: str) -> str:
        """Construye la estructura de directorios en BD a partir de una ruta del sistema de archivos"""
        import os
        
        root_path = Path(repository_path)
        if not root_path.exists():
            raise ValueError(f"La ruta del repositorio no existe: {repository_path}")
        
        # Verificar si ya existe un directorio raíz para este repositorio
        existing_root = self.directory_repo.get_root_directories(repository_name)
        if existing_root:
            logger.info(f"Ya existe estructura de directorios para {repository_name}, usando directorio existente")
            return existing_root[0].id
        
        # Crear directorio raíz solo si no existe
        root_directory = NSDKDirectory(
            name=root_path.name,
            path=str(root_path),
            repository_name=repository_name,
            parent_id=None,
            level=0
        )
        
        root_dir = self.directory_repo.create_directory(root_directory)
        
        # Construir árbol recursivamente
        self._build_directory_tree_recursive(root_path, root_dir.id, repository_name, 1)
        
        return root_dir.id
    
    def _build_directory_tree_recursive(self, current_path: Path, parent_id: str, repository_name: str, level: int):
        """Construye recursivamente la estructura de directorios"""
        try:
            for item in current_path.iterdir():
                if item.is_dir():
                    # Crear directorio
                    directory = NSDKDirectory(
                        name=item.name,
                        path=str(item),
                        repository_name=repository_name,
                        parent_id=parent_id,
                        level=level
                    )
                    
                    created_dir = self.directory_repo.create_directory(directory)
                    
                    # Recursión para subdirectorios
                    self._build_directory_tree_recursive(item, created_dir.id, repository_name, level + 1)
                    
                    # Actualizar estadísticas del directorio padre
                    self._update_parent_stats(parent_id)
        
        except PermissionError:
            # Ignorar directorios sin permisos
            pass
    
    def _update_parent_stats(self, parent_id: str):
        """Actualiza las estadísticas de un directorio padre"""
        try:
            children = self.directory_repo.get_children_by_parent_id(parent_id)
            files_in_children = self.file_repo.get_files_by_directory_ids([c.id for c in children])
            
            total_file_count = len(files_in_children)
            total_dir_count = len(children)
            total_size = sum(f.size_kb for f in files_in_children)
            
            self.directory_repo.update_directory_stats(parent_id, total_file_count, total_dir_count, total_size)
        except Exception:
            pass
    
    def get_directory_contents_by_id(self, directory_id: str) -> Dict[str, Any]:
        """Obtiene el contenido completo de un directorio por ID"""
        directory = self.directory_repo.get_directory_by_id(directory_id)
        if not directory:
            return None
        
        # Obtener subdirectorios
        subdirectories = self.directory_repo.get_children_by_parent_id(directory_id)
        
        # Obtener archivos en este directorio
        files = self.file_repo.get_files_by_directory_id(directory_id)
        
        # Convertir a estructura de árbol
        result = {
            'directory': {
                'id': directory.id,
                'name': directory.name,
                'path': directory.path,
                'repository_name': directory.repository_name,
                'parent_id': directory.parent_id,
                'level': directory.level,
                'file_count': directory.file_count,
                'dir_count': directory.dir_count,
                'total_size_kb': directory.total_size_kb,
                'created_at': directory.created_at.isoformat() if directory.created_at else None,
                'updated_at': directory.updated_at.isoformat() if directory.updated_at else None
            },
            'children': []
        }
        
        # Agregar subdirectorios
        for subdir in subdirectories:
            result['children'].append({
                'id': subdir.id,
                'name': subdir.name,
                'type': 'directory',
                'path': subdir.path,
                'is_file': False,
                'is_dir': True,
                'file_count': subdir.file_count,
                'dir_count': subdir.dir_count,
                'size_kb': subdir.total_size_kb,
                'expandable': True,
                'children': []
            })
        
        # Agregar archivos
        for file in files:
            result['children'].append({
                'id': file.id,
                'name': file.file_name,
                'type': file.file_type,
                'path': file.file_path,
                'is_file': True,
                'is_dir': False,
                'line_count': file.line_count,
                'char_count': file.char_count,
                'size_kb': file.size_kb,
                'function_count': file.function_count,
                'functions': file.functions,
                'field_count': file.field_count,
                'fields': file.fields,
                'button_count': file.button_count,
                'buttons': file.buttons,
                'expandable': False,
                'children': []
            })
        
        return result
    
    def get_root_structure(self, repository_name: str) -> Dict[str, Any]:
        """Obtiene solo la estructura raíz del repositorio (nivel 0)"""
        try:
            # Obtener solo directorios de nivel 0 (sin parent_id)
            root_directories = self.directory_repo.get_directories_by_level(repository_name, 0)
            
            # Convertir a estructura simple
            children = []
            for directory in root_directories:
                children.append({
                    'id': directory.id,
                    'name': directory.name,
                    'type': 'directory',
                    'path': directory.path,
                    'is_file': False,
                    'is_dir': True,
                    'file_count': directory.file_count,
                    'dir_count': directory.dir_count,
                    'size_kb': directory.total_size_kb,
                    'children': []  # No cargar hijos aquí para lazy loading
                })
            
            return {
                'repository_name': repository_name,
                'children': children
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo estructura raíz del repositorio {repository_name}: {str(e)}")
            raise
