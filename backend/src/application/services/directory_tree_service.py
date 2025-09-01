from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
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
            logger.info(f"Ya existe estructura de directorios para {repository_name}, añadiendo solo directorios nuevos")
            root_dir_id = existing_root[0].id
        else:
            # Crear directorio raíz solo si no existe
            root_directory = NSDKDirectory(
                name=root_path.name,
                path=str(root_path),
                repository_name=repository_name,
                parent_id=None,
                level=0
            )
            root_dir = self.directory_repo.create_directory(root_directory)
            root_dir_id = root_dir.id
            logger.info(f"Directorio raíz creado para {repository_name}")
        
        # Construir árbol recursivamente (solo añadirá lo que falta)
        self._build_directory_tree_recursive(root_path, root_dir_id, repository_name, 1)
        
        return root_dir_id
    
    def _build_directory_tree_recursive(self, current_path: Path, parent_id: str, repository_name: str, level: int):
        """Construye recursivamente la estructura de directorios"""
        try:
            for item in current_path.iterdir():
                if item.is_dir():
                    # Verificar si el directorio ya existe en la BD
                    existing_dir = self.directory_repo.get_directory_by_path(str(item), repository_name)
                    
                    if existing_dir:
                        logger.info(f"Directorio ya existe en BD: {item.name}, usando existente")
                        created_dir = existing_dir
                    else:
                        # Crear directorio solo si no existe
                        directory = NSDKDirectory(
                            name=item.name,
                            path=str(item),
                            repository_name=repository_name,
                            parent_id=parent_id,
                            level=level
                        )
                        
                        created_dir = self.directory_repo.create_directory(directory)
                        logger.info(f"Directorio creado: {item.name}")
                    
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
                'analysis_status': file.analysis_status,  # ← AÑADIR ESTE CAMPO
                'analysis_date': file.analysis_date.isoformat() if file.analysis_date else None,  # ← AÑADIR ESTE CAMPO
                'expandable': False,
                'children': []
            })
        
        # Fallback: si la BD no tiene archivos para este directorio, listar archivos del disco
        try:
            # Construir set de paths ya incluidos para evitar duplicados
            existing_file_paths = set()
            for child in result['children']:
                if child.get('is_file'):
                    existing_file_paths.add(child.get('path'))

            dir_path = Path(directory.path)
            if dir_path.exists() and dir_path.is_dir():
                for item in dir_path.iterdir():
                    # Solo archivos inmediatos (no recursivo)
                    if item.is_file():
                        file_path_str = str(item)
                        if file_path_str in existing_file_paths:
                            continue
                        # Añadir archivo del disco con metadatos mínimos
                        try:
                            size_kb = round(item.stat().st_size / 1024.0, 2)
                        except Exception:
                            size_kb = None
                        # Buscar si existe análisis en BD para este archivo
                        file_analysis = self.file_repo.get_by_file_path(file_path_str, directory.repository_name)
                        logger.info(f"Buscando archivo {item.name} en BD: {'encontrado' if file_analysis else 'no encontrado'}")
                        
                        # Si no existe y es un archivo .SCR, crear registro automáticamente
                        if not file_analysis and item.name.upper().endswith('.SCR'):
                            logger.info(f"Creando registro automático para archivo .SCR: {item.name}")
                            from ...domain.entities.nsdk_file_analysis import NSDKFileAnalysis
                            from datetime import datetime
                            
                            try:
                                # Leer contenido para obtener metadatos básicos
                                content = item.read_text(encoding='utf-8', errors='ignore')
                                lines = content.split('\n')
                                
                                new_analysis = NSDKFileAnalysis(
                                    file_path=file_path_str,
                                    file_name=item.name,
                                    file_type='screen',
                                    repository_name=directory.repository_name,
                                    line_count=len(lines),
                                    char_count=len(content),
                                    size_kb=size_kb,
                                    function_count=0,
                                    functions=[],
                                    field_count=0,
                                    fields=[],
                                    button_count=0,
                                    buttons=[],
                                    analysis_status='pending',
                                    analysis_date=datetime.utcnow()
                                )
                                
                                file_analysis = self.file_repo.create(new_analysis)
                                logger.info(f"Registro automático creado para {item.name}")
                                
                            except Exception as e:
                                logger.warning(f"No se pudo crear registro automático para {item.name}: {str(e)}")
                        
                        file_id = file_analysis.id if file_analysis else None
                        logger.info(f"Archivo {item.name} - ID asignado: {file_id}")
                        
                        result['children'].append({
                            'id': file_id,
                            'name': item.name,
                            'type': 'screen' if item.name.upper().endswith('.SCR') else 'other',
                            'path': file_path_str,
                            'is_file': True,
                            'is_dir': False,
                            'size_kb': size_kb,
                            'analysis_status': file_analysis.analysis_status if file_analysis else 'pending',  # ← AÑADIR ESTE CAMPO
                            'analysis_date': file_analysis.analysis_date.isoformat() if file_analysis and file_analysis.analysis_date else None,  # ← AÑADIR ESTE CAMPO
                            'expandable': False,
                            'children': []
                        })
        except Exception as e:
            logger.warning(f"Fallback de listado de archivos en disco falló para {directory.path}: {str(e)}")
        
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
