from ..dto.configuration_dto import ConfigurationDTO
from ...infrastructure.services.repository_manager_service import RepositoryManagerService
from ...infrastructure.services.llm_service_impl import LLMServiceImpl
from ...infrastructure.services.vector_store_service_impl import VectorStoreServiceImpl

class TestConnectionsUseCase:
    def __init__(self, repository_manager: RepositoryManagerService):
        self.repository_manager = repository_manager
    
    def execute(self, config_data: dict):
        results = []
        
        # Repositorios - REUTILIZANDO RepositoryManagerService
        for key, label in [
            ("sourceRepo", "Repositorio Origen (NSDK)"),
            ("frontendRepo", "Repositorio Frontend (Angular)"),
            ("backendRepo", "Repositorio Backend (Spring Boot)")
        ]:
            repo = config_data.get(key, {})
            if repo and repo.get('url'):
                ok, msg = self._test_repository_connection(repo, label)
            else:
                ok, msg = True, f"{label}: No configurado (opcional)"
            results.append({"service": label, "status": "success" if ok else "error", "message": msg})
        
        # LLM
        llm = config_data.get("llmConfig", {})
        if llm and (llm.get('provider') or llm.get('apiKey')):
            ok, msg = LLMServiceImpl.test_connection(llm)
        else:
            ok, msg = True, "LLM Provider: No configurado (opcional)"
        results.append({"service": "LLM Provider", "status": "success" if ok else "error", "message": msg})
        
        # Vector Store
        vector = config_data.get("vectorStoreConfig", {})
        if vector and (vector.get('type') or vector.get('connectionString')):
            ok, msg = VectorStoreServiceImpl.test_connection(vector)
        else:
            ok, msg = True, "Vector Store: No configurado (opcional)"
        results.append({"service": "Vector Store", "status": "success" if ok else "error", "message": msg})
        
        return results
    
    def _test_repository_connection(self, repo_config: dict, repo_label: str) -> tuple[bool, str]:
        """Prueba la conexión a un repositorio usando git ls-remote (más eficiente)"""
        try:
            url = repo_config.get('url', '').strip()
            branch = repo_config.get('branch', 'main').strip()
            username = repo_config.get('username', '').strip()
            token = repo_config.get('token', '').strip()
            
            if not url:
                return False, f"{repo_label}: URL no proporcionada"
            
            # Construir URL con credenciales si se proporcionan
            if username and token:
                # Escapar caracteres especiales en username y token
                safe_username = username.replace('@', '%40').replace(':', '%3A')
                safe_token = token.replace('@', '%40').replace(':', '%3A')
                test_url = url.replace('https://', f'https://{safe_username}:{safe_token}@')
            else:
                test_url = url
            
            try:
                # Usar git ls-remote para probar conexión (mucho más rápido)
                import subprocess
                import tempfile
                import os
                
                # Crear directorio temporal
                temp_dir = tempfile.mkdtemp()
                
                try:
                    # Ejecutar git ls-remote para verificar conectividad
                    result = subprocess.run(
                        ['git', 'ls-remote', '--heads', test_url, branch],
                        capture_output=True,
                        text=True,
                        cwd=temp_dir,
                        timeout=30  # Timeout de 30 segundos
                    )
                    
                    if result.returncode == 0:
                        # Verificar que la rama existe
                        if result.stdout.strip():
                            return True, f"{repo_label}: Conexión exitosa (rama {branch} encontrada)"
                        else:
                            return False, f"{repo_label}: Rama {branch} no encontrada"
                    else:
                        # Error en git ls-remote
                        error_msg = result.stderr.strip() or "Error desconocido"
                        return False, f"{repo_label}: {error_msg}"
                        
                finally:
                    # Limpiar directorio temporal
                    import shutil
                    shutil.rmtree(temp_dir, ignore_errors=True)
                    
            except subprocess.TimeoutExpired:
                return False, f"{repo_label}: Timeout - la operación tardó demasiado"
            except FileNotFoundError:
                return False, f"{repo_label}: Git no está instalado en el sistema"
            except Exception as e:
                return False, f"{repo_label}: Error en git ls-remote - {str(e)}"
                
        except Exception as e:
            return False, f"{repo_label}: Error inesperado - {str(e)}" 