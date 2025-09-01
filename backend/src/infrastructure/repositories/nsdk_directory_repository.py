from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from src.domain.entities.nsdk_directory import NSDKDirectory, NSDKDirectoryModel
import uuid

class NSDKDirectoryRepository:
    """Repositorio para manejar directorios NSDK"""
    
    def __init__(self, db_session: Session):
        self.db_session = db_session
    
    def create_directory(self, directory: NSDKDirectory) -> NSDKDirectory:
        """Crea un nuevo directorio"""
        if not directory.id:
            directory.id = str(uuid.uuid4())
        
        db_directory = NSDKDirectoryModel(
            id=directory.id,
            name=directory.name,
            path=directory.path,
            repository_name=directory.repository_name,
            parent_id=directory.parent_id,
            level=directory.level,
            file_count=directory.file_count,
            dir_count=directory.dir_count,
            total_size_kb=directory.total_size_kb
        )
        
        self.db_session.add(db_directory)
        self.db_session.commit()
        self.db_session.refresh(db_directory)
        
        return NSDKDirectory(
            id=db_directory.id,
            name=db_directory.name,
            path=db_directory.path,
            repository_name=db_directory.repository_name,
            parent_id=db_directory.parent_id,
            level=db_directory.level,
            file_count=db_directory.file_count,
            dir_count=db_directory.dir_count,
            total_size_kb=db_directory.total_size_kb,
            created_at=db_directory.created_at,
            updated_at=db_directory.updated_at
        )
    
    def get_directory_by_id(self, directory_id: str) -> Optional[NSDKDirectory]:
        """Obtiene un directorio por ID"""
        db_directory = self.db_session.query(NSDKDirectoryModel).filter(
            NSDKDirectoryModel.id == directory_id
        ).first()
        
        if not db_directory:
            return None
        
        return NSDKDirectory(
            id=db_directory.id,
            name=db_directory.name,
            path=db_directory.path,
            repository_name=db_directory.repository_name,
            parent_id=db_directory.parent_id,
            level=db_directory.level,
            file_count=db_directory.file_count,
            dir_count=db_directory.dir_count,
            total_size_kb=db_directory.total_size_kb,
            created_at=db_directory.created_at,
            updated_at=db_directory.updated_at
        )
    
    def get_directory_by_path(self, path: str, repository_name: str) -> Optional[NSDKDirectory]:
        """Obtiene un directorio por su ruta completa y repositorio"""
        db_directory = self.db_session.query(NSDKDirectoryModel).filter(
            and_(
                NSDKDirectoryModel.path == path,
                NSDKDirectoryModel.repository_name == repository_name
            )
        ).first()
        
        if not db_directory:
            return None
        
        return NSDKDirectory(
            id=db_directory.id,
            name=db_directory.name,
            path=db_directory.path,
            repository_name=db_directory.repository_name,
            parent_id=db_directory.parent_id,
            level=db_directory.level,
            file_count=db_directory.file_count,
            dir_count=db_directory.dir_count,
            total_size_kb=db_directory.total_size_kb,
            created_at=db_directory.created_at,
            updated_at=db_directory.updated_at
        )
    
    def get_children_by_parent_id(self, parent_id: str) -> List[NSDKDirectory]:
        """Obtiene los hijos directos de un directorio"""
        try:
            models = self.db_session.query(NSDKDirectoryModel).filter(
                NSDKDirectoryModel.parent_id == parent_id
            ).all()
            
            return [
                NSDKDirectory(
                    id=dir.id,
                    name=dir.name,
                    path=dir.path,
                    repository_name=dir.repository_name,
                    parent_id=dir.parent_id,
                    level=dir.level,
                    file_count=dir.file_count,
                    dir_count=dir.dir_count,
                    total_size_kb=dir.total_size_kb,
                    created_at=dir.created_at,
                    updated_at=dir.updated_at
                )
                for dir in models
            ]
            
        except Exception as e:
            # logger.error(f"Error obteniendo hijos del directorio {parent_id}: {str(e)}") # Original code had logger, but logger is not defined.
            return []
    
    def get_directories_by_level(self, repository_name: str, level: int) -> List[NSDKDirectory]:
        """Obtiene directorios de un nivel específico"""
        try:
            # Usar DISTINCT para evitar duplicados por nombre y ruta
            models = self.db_session.query(NSDKDirectoryModel).filter(
                and_(
                    NSDKDirectoryModel.repository_name == repository_name,
                    NSDKDirectoryModel.level == level
                )
            ).distinct(NSDKDirectoryModel.name, NSDKDirectoryModel.path).all()
            
            return [
                NSDKDirectory(
                    id=dir.id,
                    name=dir.name,
                    path=dir.path,
                    repository_name=dir.repository_name,
                    parent_id=dir.parent_id,
                    level=dir.level,
                    file_count=dir.file_count,
                    dir_count=dir.dir_count,
                    total_size_kb=dir.total_size_kb,
                    created_at=dir.created_at,
                    updated_at=dir.updated_at
                )
                for dir in models
            ]
            
        except Exception as e:
            # logger.error(f"Error obteniendo directorios de nivel {level} en {repository_name}: {str(e)}") # Original code had logger, but logger is not defined.
            return []
    
    def get_root_directories(self, repository_name: str) -> List[NSDKDirectory]:
        """Obtiene los directorios raíz de un repositorio"""
        db_directories = self.db_session.query(NSDKDirectoryModel).filter(
            and_(
                NSDKDirectoryModel.repository_name == repository_name,
                NSDKDirectoryModel.parent_id.is_(None)
            )
        ).all()
        
        return [
            NSDKDirectory(
                id=dir.id,
                name=dir.name,
                path=dir.path,
                repository_name=dir.repository_name,
                parent_id=dir.parent_id,
                level=dir.level,
                file_count=dir.file_count,
                dir_count=dir.dir_count,
                total_size_kb=dir.total_size_kb,
                created_at=dir.created_at,
                updated_at=dir.updated_at
            )
            for dir in db_directories
        ]
    
    def get_directory_tree_by_id(self, directory_id: str, max_depth: int = 3) -> Dict[str, Any]:
        """Obtiene el árbol de directorios a partir de un ID específico"""
        directory = self.get_directory_by_id(directory_id)
        if not directory:
            return None
        
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
        
        if max_depth > 0:
            children = self.get_children_by_parent_id(directory_id)
            for child in children:
                child_tree = self.get_directory_tree_by_id(child.id, max_depth - 1)
                if child_tree:
                    result['children'].append(child_tree)
        
        return result
    
    def update_directory_stats(self, directory_id: str, file_count: int, dir_count: int, total_size_kb: float) -> bool:
        """Actualiza las estadísticas de un directorio"""
        try:
            db_directory = self.db_session.query(NSDKDirectoryModel).filter(
                NSDKDirectoryModel.id == directory_id
            ).first()
            
            if db_directory:
                db_directory.file_count = file_count
                db_directory.dir_count = dir_count
                db_directory.total_size_kb = total_size_kb
                self.db_session.commit()
                return True
            
            return False
        except Exception:
            self.db_session.rollback()
            return False
    

