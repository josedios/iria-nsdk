import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from git import Repo, GitCommandError
import logging

logger = logging.getLogger(__name__)

class RepositoryManagerService:
    """Servicio para gestionar repositorios clonados permanentemente"""
    
    def __init__(self, repositories_dir: str = None):
        # Si no se especifica, usar ruta local para desarrollo
        if repositories_dir is None:
            # Detectar si estamos en Docker o en desarrollo local
            import os
            if os.name == 'nt':  # Windows
                # Desarrollo local en Windows
                repositories_dir = str(Path.cwd() / "repositories")
            elif Path("/app").exists():
                repositories_dir = "/app/repositories"  # Docker
            else:
                # Desarrollo local en Linux/Mac
                repositories_dir = str(Path.cwd() / "repositories")
        
        self.repositories_dir = Path(repositories_dir)
        self.repositories_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Directorio de repositorios: {self.repositories_dir}")
    
    def get_repository_path(self, repo_name: str) -> Path:
        """Obtiene la ruta del repositorio clonado"""
        return self.repositories_dir / repo_name
    
    def is_repository_cloned(self, repo_name: str) -> bool:
        """Verifica si un repositorio ya está clonado"""
        repo_path = self.get_repository_path(repo_name)
        return repo_path.exists() and (repo_path / ".git").exists()
    
    def clone_repository(self, repo_url: str, repo_name: str, branch: str = 'main',
                        username: Optional[str] = None, token: Optional[str] = None) -> Path:
        """
        Clona un repositorio permanentemente
        
        Args:
            repo_url: URL del repositorio
            repo_name: Nombre del directorio local
            branch: Rama a clonar
            username: Usuario para autenticación
            token: Token para autenticación
            
        Returns:
            Path: Ruta del repositorio clonado
        """
        try:
            repo_path = self.get_repository_path(repo_name)
            
            # Si ya existe, hacer pull en lugar de clonar
            if self.is_repository_cloned(repo_name):
                logger.info(f"Repositorio {repo_name} ya existe, actualizando...")
                return self.update_repository(repo_name, branch)
            
            # Construir URL con credenciales si se proporcionan
            if username and token:
                # Escapar caracteres especiales en username y token
                safe_username = username.replace('@', '%40').replace(':', '%3A')
                safe_token = token.replace('@', '%40').replace(':', '%3A')
                clone_url = repo_url.replace('https://', f'https://{safe_username}:{safe_token}@')
            else:
                clone_url = repo_url
            
            logger.info(f"Clonando repositorio: {repo_url} -> {repo_path}")
            
            # Clonar repositorio
            repo = Repo.clone_from(
                clone_url,
                repo_path,
                branch=branch,
                depth=1  # Solo el commit más reciente para ahorrar espacio
            )
            
            logger.info(f"Repositorio clonado exitosamente en: {repo_path}")
            return repo_path
            
        except GitCommandError as e:
            logger.error(f"Error clonando repositorio: {str(e)}")
            raise Exception(f"Error clonando repositorio: {str(e)}")
        except Exception as e:
            logger.error(f"Error inesperado clonando repositorio: {str(e)}")
            raise Exception(f"Error inesperado: {str(e)}")
    
    def update_repository(self, repo_name: str, branch: str = 'main') -> Path:
        """Actualiza un repositorio existente"""
        try:
            repo_path = self.get_repository_path(repo_name)
            if not self.is_repository_cloned(repo_name):
                raise Exception(f"Repositorio {repo_name} no está clonado")
            
            repo = Repo(repo_path)
            
            # Cambiar a la rama especificada
            current_branch = repo.active_branch.name
            if current_branch != branch:
                logger.info(f"Cambiando de rama {current_branch} a {branch}")
                repo.git.checkout(branch)
            
            # Hacer pull para obtener cambios
            logger.info(f"Actualizando repositorio {repo_name}...")
            repo.git.pull()
            
            logger.info(f"Repositorio {repo_name} actualizado exitosamente")
            return repo_path
            
        except Exception as e:
            logger.error(f"Error actualizando repositorio {repo_name}: {str(e)}")
            raise Exception(f"Error actualizando repositorio: {str(e)}")
    
    def get_repository_info(self, repo_name: str) -> Dict[str, Any]:
        """Obtiene información del repositorio"""
        try:
            repo_path = self.get_repository_path(repo_name)
            if not self.is_repository_cloned(repo_name):
                return {}
            
            repo = Repo(repo_path)
            
            return {
                'name': repo_name,
                'path': str(repo_path),
                'active_branch': repo.active_branch.name,
                'last_commit': {
                    'hash': repo.head.commit.hexsha[:8],
                    'message': repo.head.commit.message.strip(),
                    'author': repo.head.commit.author.name,
                    'date': repo.head.commit.committed_datetime.isoformat()
                },
                'remote_url': repo.remotes.origin.url if repo.remotes else None,
                'status': 'clean' if not repo.is_dirty() else 'dirty'
            }
            
        except Exception as e:
            logger.error(f"Error obteniendo información del repositorio {repo_name}: {str(e)}")
            return {}
    
    def list_repositories(self) -> List[Dict[str, Any]]:
        """Lista todos los repositorios clonados"""
        repositories = []
        
        try:
            for item in self.repositories_dir.iterdir():
                if item.is_dir() and (item / ".git").exists():
                    repo_info = self.get_repository_info(item.name)
                    if repo_info:
                        repositories.append(repo_info)
            
            return repositories
            
        except Exception as e:
            logger.error(f"Error listando repositorios: {str(e)}")
            return []
    
    def delete_repository(self, repo_name: str) -> bool:
        """Elimina un repositorio clonado"""
        try:
            repo_path = self.get_repository_path(repo_name)
            if not repo_path.exists():
                return True
            
            logger.info(f"Eliminando repositorio: {repo_path}")
            shutil.rmtree(repo_path)
            logger.info(f"Repositorio {repo_name} eliminado exitosamente")
            return True
            
        except Exception as e:
            logger.error(f"Error eliminando repositorio {repo_name}: {str(e)}")
            return False
    
    def get_nsdk_modules(self, repo_name: str) -> List[Dict[str, Any]]:
        """
        Descubre módulos NSDK en un repositorio y los organiza en estructura de árbol
        
        Returns:
            Lista de módulos organizados jerárquicamente
        """
        try:
            repo_path = self.get_repository_path(repo_name)
            if not self.is_repository_cloned(repo_name):
                return []
            
            modules = []
            
            # Buscar archivos .NCL (módulos)
            ncl_files = list(repo_path.rglob("*.NCL")) + list(repo_path.rglob("*.ncl"))
            
            for ncl_file in ncl_files:
                try:
                    # Leer contenido del archivo
                    with open(ncl_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Extraer nombre del módulo
                    module_name = self._extract_module_name(content, ncl_file.name)
                    
                    # Calcular estadísticas básicas
                    lines = content.split('\n')
                    line_count = len(lines)
                    char_count = len(content)
                    
                    # Buscar funciones
                    functions = self._extract_functions(content)
                    
                    # Crear estructura jerárquica
                    relative_path = ncl_file.relative_to(repo_path)
                    path_parts = relative_path.parts
                    
                    module_info = {
                        'name': module_name,
                        'file_path': str(relative_path),
                        'file_name': ncl_file.name,
                        'line_count': line_count,
                        'char_count': char_count,
                        'function_count': len(functions),
                        'functions': functions[:10],  # Solo las primeras 10 funciones
                        'size_kb': round(os.path.getsize(ncl_file) / 1024, 2),
                        'path_parts': path_parts,  # Partes de la ruta para construir el árbol
                        'depth': len(path_parts) - 1,  # Profundidad en el árbol
                        'is_file': True,
                        'type': 'module'
                    }
                    
                    modules.append(module_info)
                    
                except Exception as e:
                    logger.warning(f"Error procesando archivo {ncl_file}: {str(e)}")
                    continue
            
            logger.info(f"Encontrados {len(modules)} módulos NSDK en {repo_name}")
            return modules
            
        except Exception as e:
            logger.error(f"Error obteniendo módulos NSDK de {repo_name}: {str(e)}")
            return []
    
    def get_repository_tree(self, repo_name: str) -> Dict[str, Any]:
        """
        Genera una estructura de árbol completa del repositorio
        
        Returns:
            Estructura de árbol con directorios y archivos
        """
        try:
            repo_path = self.get_repository_path(repo_name)
            if not self.is_repository_cloned(repo_name):
                return {}
            
            def build_tree(path: Path, current_depth: int = 0, max_depth: int = 5) -> Dict[str, Any]:
                """Construye recursivamente la estructura del árbol"""
                if current_depth > max_depth:
                    return {}
                
                result = {
                    'name': path.name,
                    'path': str(path.relative_to(repo_path)),
                    'is_file': path.is_file(),
                    'is_dir': path.is_dir(),
                    'depth': current_depth,
                    'children': [],
                    'type': 'directory' if path.is_dir() else self._get_file_type(path)
                }
                
                if path.is_dir():
                    # Agregar información del directorio
                    result['file_count'] = len(list(path.glob('*')))
                    result['dir_count'] = len([x for x in path.iterdir() if x.is_dir()])
                    
                    # Procesar subdirectorios y archivos
                    for item in sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                        if item.name.startswith('.'):  # Ignorar archivos ocultos
                            continue
                        
                        child = build_tree(item, current_depth + 1, max_depth)
                        if child:
                            result['children'].append(child)
                
                elif path.is_file():
                    # Agregar información del archivo
                    result['size_kb'] = round(path.stat().st_size / 1024, 2)
                    result['extension'] = path.suffix.lower()
                    
                    # Si es un archivo NSDK, agregar información específica
                    if path.suffix.lower() in ['.ncl', '.scr', '.inc', '.prg']:
                        result.update(self._get_nsdk_file_info(path))
                
                return result
            
            # Construir el árbol desde la raíz del repositorio
            tree = build_tree(repo_path)
            logger.info(f"Árbol del repositorio {repo_name} generado exitosamente")
            return tree
            
        except Exception as e:
            logger.error(f"Error generando árbol del repositorio {repo_name}: {str(e)}")
            return {}
    
    def _get_file_type(self, file_path: Path) -> str:
        """Determina el tipo de archivo"""
        suffix = file_path.suffix.lower()
        if suffix in ['.ncl']:
            return 'module'
        elif suffix in ['.scr']:
            return 'screen'
        elif suffix in ['.inc']:
            return 'include'
        elif suffix in ['.prg']:
            return 'program'
        elif suffix in ['.ora', '.ora_pre']:
            return 'config'
        elif suffix in ['.md', '.txt', '.bat']:
            return 'document'
        else:
            return 'other'
    
    def _get_nsdk_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Obtiene información específica de archivos NSDK"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            lines = content.split('\n')
            line_count = len(lines)
            char_count = len(content)
            
            info = {
                'line_count': line_count,
                'char_count': char_count,
                'size_kb': round(file_path.stat().st_size / 1024, 2)
            }
            
            # Información específica según el tipo
            suffix = file_path.suffix.lower()
            if suffix == '.ncl':
                info['functions'] = self._extract_functions(content)[:10]
                info['function_count'] = len(info['functions'])
            elif suffix == '.scr':
                info['fields'] = self._extract_fields(content)[:10]
                info['buttons'] = self._extract_buttons(content)[:10]
                info['field_count'] = len(info['fields'])
                info['button_count'] = len(info['buttons'])
            
            return info
            
        except Exception as e:
            logger.warning(f"Error obteniendo información del archivo {file_path}: {str(e)}")
            return {}
    
    def _extract_module_name(self, content: str, filename: str) -> str:
        """Extrae el nombre del módulo del contenido del archivo"""
        # Buscar declaración MODULE
        import re
        module_match = re.search(r'MODULE\s+(\w+)', content, re.IGNORECASE)
        if module_match:
            return module_match.group(1)
        
        # Si no hay declaración MODULE, usar el nombre del archivo
        return filename.replace('.NCL', '').replace('.ncl', '')
    
    def _extract_functions(self, content: str) -> List[str]:
        """Extrae nombres de funciones del contenido del archivo"""
        import re
        functions = re.findall(r'FUNCTION\s+(\w+)', content, re.IGNORECASE)
        return functions
    
    def get_nsdk_screens(self, repo_name: str) -> List[Dict[str, Any]]:
        """
        Descubre pantallas NSDK en un repositorio
        
        Returns:
            Lista de pantallas encontradas
        """
        try:
            repo_path = self.get_repository_path(repo_name)
            if not self.is_repository_cloned(repo_name):
                return []
            
            screens = []
            
            # Buscar archivos .SCR (pantallas)
            scr_files = list(repo_path.rglob("*.SCR")) + list(repo_path.rglob("*.scr"))
            
            for scr_file in scr_files:
                try:
                    # Leer contenido del archivo
                    with open(scr_file, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Extraer nombre de la pantalla
                    screen_name = self._extract_screen_name(content, scr_file.name)
                    
                    # Calcular estadísticas básicas
                    lines = content.split('\n')
                    line_count = len(lines)
                    char_count = len(content)
                    
                    # Buscar campos y botones
                    fields = self._extract_fields(content)
                    buttons = self._extract_buttons(content)
                    
                    screen_info = {
                        'name': screen_name,
                        'file_path': str(scr_file.relative_to(repo_path)),
                        'file_name': scr_file.name,
                        'line_count': line_count,
                        'char_count': char_count,
                        'field_count': len(fields),
                        'fields': fields[:10],  # Solo los primeros 10 campos
                        'button_count': len(buttons),
                        'buttons': buttons[:10],  # Solo los primeros 10 botones
                        'size_kb': round(os.path.getsize(scr_file) / 1024, 2)
                    }
                    
                    screens.append(screen_info)
                    
                except Exception as e:
                    logger.warning(f"Error procesando archivo {scr_file}: {str(e)}")
                    continue
            
            logger.info(f"Encontradas {len(screens)} pantallas NSDK en {repo_name}")
            return screens
            
        except Exception as e:
            logger.error(f"Error obteniendo pantallas NSDK de {repo_name}: {str(e)}")
            return []
    
    def _extract_screen_name(self, content: str, filename: str) -> str:
        """Extrae el nombre de la pantalla del contenido del archivo"""
        # Buscar declaración SCREEN
        import re
        screen_match = re.search(r'SCREEN\s+(\w+)', content, re.IGNORECASE)
        if screen_match:
            return screen_match.group(1)
        
        # Si no hay declaración SCREEN, usar el nombre del archivo
        return filename.replace('.SCR', '').replace('.scr', '')
    
    def _extract_fields(self, content: str) -> List[str]:
        """Extrae nombres de campos del contenido del archivo"""
        import re
        fields = re.findall(r'FIELD\s+(\w+)', content, re.IGNORECASE)
        return fields
    
    def _extract_buttons(self, content: str) -> List[str]:
        """Extrae nombres de botones del contenido del archivo"""
        import re
        buttons = re.findall(r'BUTTON\s+(\w+)', content, re.IGNORECASE)
        return buttons
