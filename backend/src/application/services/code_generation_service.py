from typing import Dict, Any, Optional, List
import logging
import json
import os
import tempfile
import shutil
from pathlib import Path
from ..use_cases.vectorization_use_case import VectorizationUseCase
from ...infrastructure.services.llm_service_impl import LLMServiceImpl
from ...infrastructure.services.vector_store_service_impl import VectorStoreServiceImpl
from .nsdk_query_service import NSDKQueryService

logger = logging.getLogger(__name__)

class CodeGenerationService:
    """Servicio para generar código fuente a partir de análisis de IA"""
    
    def __init__(self, vectorization_use_case: VectorizationUseCase, llm_service: LLMServiceImpl, nsdk_query_service: NSDKQueryService = None):
        self.vectorization_use_case = vectorization_use_case
        self.llm_service = llm_service
        self.nsdk_query_service = nsdk_query_service
    
    async def generate_code_from_analysis(
        self, 
        analysis_data: Dict[str, Any], 
        file_name: str,
        frontend_repo_path: str,
        backend_repo_path: str
    ) -> Dict[str, Any]:
        """
        Genera código fuente completo a partir del análisis de IA
        
        Args:
            analysis_data: Datos del análisis de IA
            file_name: Nombre del archivo .SCR
            frontend_repo_path: Ruta del repositorio frontend
            backend_repo_path: Ruta del repositorio backend
            
        Returns:
            Dict con el resultado de la generación
        """
        try:
            logger.info(f"Iniciando generación de código para {file_name}")
            
            # Validar datos de entrada antes de consumir tokens
            self._validate_analysis_data(analysis_data, file_name)
            self._validate_repository_paths(frontend_repo_path, backend_repo_path)
            
            # 1. Generar código Angular
            logger.info("1. Generando código Angular...")
            frontend_code = await self._generate_frontend_code(analysis_data, file_name)
            
            # 2. Generar código Spring Boot
            logger.info("2. Generando código Spring Boot...")
            backend_code = await self._generate_backend_code(analysis_data, file_name)
            
            # 3. Crear rama y aplicar cambios
            logger.info("3. Creando rama y aplicando cambios...")
            branch_name = f"feature/{file_name.replace('.scr', '').lower()}"
            
            # Crear rama en frontend
            frontend_result = await self._create_branch_and_commit(
                frontend_repo_path, 
                branch_name, 
                frontend_code, 
                f"feat: Generar componente {file_name.replace('.scr', '')}"
            )
            
            # Crear rama en backend
            backend_result = await self._create_branch_and_commit(
                backend_repo_path, 
                branch_name, 
                backend_code, 
                f"feat: Generar entidad y servicios para {file_name.replace('.scr', '')}"
            )
            
            return {
                "success": True,
                "file_name": file_name,
                "branch_name": branch_name,
                "frontend": {
                    "files_generated": len(frontend_code),
                    "branch_created": frontend_result["branch_created"],
                    "commit_hash": frontend_result["commit_hash"]
                },
                "backend": {
                    "files_generated": len(backend_code),
                    "branch_created": backend_result["branch_created"],
                    "commit_hash": backend_result["commit_hash"]
                },
                "message": f"Código generado exitosamente en rama {branch_name}"
            }
            
        except Exception as e:
            logger.error(f"Error generando código para {file_name}: {str(e)}")
            return {
                "success": False,
                "file_name": file_name,
                "error": str(e),
                "message": f"Error generando código: {str(e)}"
            }
    
    async def _generate_frontend_code(self, analysis_data: Dict[str, Any], file_name: str) -> Dict[str, str]:
        """Genera código Angular a partir del análisis"""
        try:
            # Preparar prompt para generación de código Angular
            frontend_prompt = self._get_frontend_generation_prompt(analysis_data, file_name)
            
            # Llamar a la IA para generar código
            messages = [
                {"role": "user", "content": frontend_prompt}
            ]
            
            ai_response = await self.llm_service.chat_completion(messages)
            
            # Procesar respuesta y extraer archivos
            frontend_files = self._extract_frontend_files(ai_response, file_name)
            
            logger.info(f"Generados {len(frontend_files)} archivos Angular")
            return frontend_files
            
        except Exception as e:
            logger.error(f"Error generando código Angular: {str(e)}")
            raise
    
    async def _generate_backend_code(self, analysis_data: Dict[str, Any], file_name: str) -> Dict[str, str]:
        """Genera código Spring Boot a partir del análisis"""
        try:
            # Preparar prompt para generación de código Spring Boot
            backend_prompt = self._get_backend_generation_prompt(analysis_data, file_name)
            
            # Llamar a la IA para generar código
            messages = [
                {"role": "user", "content": backend_prompt}
            ]
            
            ai_response = await self.llm_service.chat_completion(messages)
            
            # Procesar respuesta y extraer archivos
            backend_files = self._extract_backend_files(ai_response, file_name)
            
            logger.info(f"Generados {len(backend_files)} archivos Spring Boot")
            return backend_files
            
        except Exception as e:
            logger.error(f"Error generando código Spring Boot: {str(e)}")
            raise
    
    def _get_frontend_generation_prompt(self, analysis_data: Dict[str, Any], file_name: str) -> str:
        """Genera prompt para creación de código Angular"""
        component_name = file_name.replace('.scr', '').replace('_', '-').lower()
        class_name = file_name.replace('.scr', '').replace('_', ' ').title().replace(' ', '')
        
        # Serializar datos manejando UUIDs y otros tipos no serializables
        serialized_data = self._serialize_analysis_data(analysis_data)
        
        return f"""
Eres un experto en Angular y Angular Material. Genera código completo para migrar la pantalla {file_name} a Angular.

ANÁLISIS DE LA PANTALLA:
{json.dumps(serialized_data, indent=2, ensure_ascii=False)}

REQUISITOS:
1. Usar Angular 17+ con standalone components
2. Usar Angular Material para la UI
3. Implementar Reactive Forms
4. Seguir las mejores prácticas de Angular
5. Incluir validaciones según el análisis
6. Implementar navegación si es necesaria

ARCHIVOS A GENERAR:
1. {component_name}.component.ts - Componente principal
2. {component_name}.component.html - Template HTML
3. {component_name}.component.scss - Estilos
4. {component_name}.service.ts - Servicio para lógica de negocio
5. {component_name}.model.ts - Interfaces TypeScript

FORMATO DE RESPUESTA:
Responde ÚNICAMENTE con un JSON que contenga los archivos generados:

{{
    "component_ts": "código del componente TypeScript",
    "component_html": "código del template HTML", 
    "component_scss": "código de los estilos SCSS",
    "service_ts": "código del servicio TypeScript",
    "model_ts": "código de las interfaces TypeScript"
}}

IMPORTANTE: 
- Usa nombres de archivo: {component_name}
- Usa nombre de clase: {class_name}
- Incluye todas las validaciones del análisis
- Implementa todos los campos identificados
- Usa Angular Material components
- Responde SOLO con el JSON, sin texto adicional
"""
    
    def _get_backend_generation_prompt(self, analysis_data: Dict[str, Any], file_name: str) -> str:
        """Genera prompt para creación de código Spring Boot"""
        entity_name = file_name.replace('.scr', '').replace('_', ' ').title().replace(' ', '')
        table_name = analysis_data.get('backend', {}).get('database_table', 'T0SIPOLI')
        
        # Serializar datos manejando UUIDs y otros tipos no serializables
        serialized_data = self._serialize_analysis_data(analysis_data)
        
        return f"""
Eres un experto en Spring Boot, JPA/Hibernate y REST APIs. Genera código completo para migrar la pantalla {file_name} a Spring Boot.

ANÁLISIS DE LA PANTALLA:
{json.dumps(serialized_data, indent=2, ensure_ascii=False)}

REQUISITOS:
1. Usar Spring Boot 3.x
2. Usar JPA/Hibernate para persistencia
3. Implementar REST API completa
4. Seguir las mejores prácticas de Spring Boot
5. Incluir validaciones según el análisis
6. Usar DTOs para transferencia de datos

ARCHIVOS A GENERAR:
1. {entity_name}.java - Entidad JPA
2. {entity_name}Repository.java - Repositorio JPA
3. {entity_name}Service.java - Servicio de negocio
4. {entity_name}Controller.java - Controlador REST
5. {entity_name}DTO.java - DTO para transferencia
6. {entity_name}RequestDTO.java - DTO para requests
7. {entity_name}ResponseDTO.java - DTO para responses

FORMATO DE RESPUESTA:
Responde ÚNICAMENTE con un JSON que contenga los archivos generados:

{{
    "entity_java": "código de la entidad JPA",
    "repository_java": "código del repositorio",
    "service_java": "código del servicio",
    "controller_java": "código del controlador REST",
    "dto_java": "código del DTO principal",
    "request_dto_java": "código del DTO de request",
    "response_dto_java": "código del DTO de response"
}}

IMPORTANTE:
- Usa nombre de entidad: {entity_name}
- Usa tabla: {table_name}
- Incluye todas las validaciones del análisis
- Implementa todos los campos identificados
- Usa anotaciones JPA correctas
- Responde SOLO con el JSON, sin texto adicional
"""
    
    def _extract_frontend_files(self, ai_response: str, file_name: str) -> Dict[str, str]:
        """Extrae archivos Angular de la respuesta de la IA"""
        try:
            import re
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'(\{.*\})', ai_response, re.DOTALL)
            if not json_match:
                raise Exception("No se encontró JSON en la respuesta de la IA")
            
            files_data = json.loads(json_match.group(1))
            
            # Mapear a rutas de archivos
            component_name = file_name.replace('.scr', '').replace('_', '-').lower()
            
            files = {}
            if 'component_ts' in files_data:
                files[f'src/app/features/{component_name}/{component_name}.component.ts'] = files_data['component_ts']
            if 'component_html' in files_data:
                files[f'src/app/features/{component_name}/{component_name}.component.html'] = files_data['component_html']
            if 'component_scss' in files_data:
                files[f'src/app/features/{component_name}/{component_name}.component.scss'] = files_data['component_scss']
            if 'service_ts' in files_data:
                files[f'src/app/features/{component_name}/{component_name}.service.ts'] = files_data['service_ts']
            if 'model_ts' in files_data:
                files[f'src/app/models/{component_name}.model.ts'] = files_data['model_ts']
            
            return files
            
        except Exception as e:
            logger.error(f"Error extrayendo archivos Angular: {str(e)}")
            raise
    
    def _extract_backend_files(self, ai_response: str, file_name: str) -> Dict[str, str]:
        """Extrae archivos Spring Boot de la respuesta de la IA"""
        try:
            import re
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'(\{.*\})', ai_response, re.DOTALL)
            if not json_match:
                raise Exception("No se encontró JSON en la respuesta de la IA")
            
            files_data = json.loads(json_match.group(1))
            
            # Mapear a rutas de archivos
            entity_name = file_name.replace('.scr', '').replace('_', ' ').title().replace(' ', '')
            package_path = "com/example/nsdk"
            
            files = {}
            if 'entity_java' in files_data:
                files[f'src/main/java/{package_path}/entity/{entity_name}.java'] = files_data['entity_java']
            if 'repository_java' in files_data:
                files[f'src/main/java/{package_path}/repository/{entity_name}Repository.java'] = files_data['repository_java']
            if 'service_java' in files_data:
                files[f'src/main/java/{package_path}/service/{entity_name}Service.java'] = files_data['service_java']
            if 'controller_java' in files_data:
                files[f'src/main/java/{package_path}/controller/{entity_name}Controller.java'] = files_data['controller_java']
            if 'dto_java' in files_data:
                files[f'src/main/java/{package_path}/dto/{entity_name}DTO.java'] = files_data['dto_java']
            if 'request_dto_java' in files_data:
                files[f'src/main/java/{package_path}/dto/{entity_name}RequestDTO.java'] = files_data['request_dto_java']
            if 'response_dto_java' in files_data:
                files[f'src/main/java/{package_path}/dto/{entity_name}ResponseDTO.java'] = files_data['response_dto_java']
            
            return files
            
        except Exception as e:
            logger.error(f"Error extrayendo archivos Spring Boot: {str(e)}")
            raise
    
    def _serialize_analysis_data(self, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serializa los datos del análisis manejando UUIDs y otros tipos no serializables"""
        import uuid
        from datetime import datetime
        
        def serialize_value(value):
            if isinstance(value, uuid.UUID):
                return str(value)
            elif isinstance(value, datetime):
                return value.isoformat()
            elif isinstance(value, dict):
                return {k: serialize_value(v) for k, v in value.items()}
            elif isinstance(value, list):
                return [serialize_value(item) for item in value]
            else:
                return value
        
        return serialize_value(analysis_data)
    
    async def generate_frontend_only(
        self, 
        analysis_data: Dict[str, Any], 
        file_name: str,
        frontend_repo_path: str
    ) -> Dict[str, Any]:
        """Genera solo código frontend a partir del análisis de IA"""
        try:
            logger.info(f"Iniciando generación de código frontend para {file_name}")
            
            # Validar datos de entrada antes de consumir tokens
            self._validate_analysis_data(analysis_data, file_name)
            self._validate_repository_paths(frontend_repo_path, frontend_repo_path)  # Usar el mismo path para validación
            
            # Generar código Angular
            logger.info("Generando código Angular...")
            frontend_code = await self._generate_frontend_code(analysis_data, file_name)
            
            # Crear rama y aplicar cambios
            logger.info("Creando rama y aplicando cambios...")
            branch_name = f"feature/{file_name.replace('.scr', '').lower()}"
            
            # Crear rama en frontend
            frontend_result = await self._create_branch_and_commit(
                frontend_repo_path, 
                branch_name, 
                frontend_code, 
                f"feat: Generar componente frontend {file_name.replace('.scr', '')}"
            )
            
            return {
                "success": True,
                "file_name": file_name,
                "frontend": {
                    "files_generated": len(frontend_code),
                    "branch_created": frontend_result["branch_created"],
                    "commit_hash": frontend_result["commit_hash"]
                },
                "message": f"Código frontend generado exitosamente en rama {branch_name}"
            }
            
        except Exception as e:
            logger.error(f"Error generando código frontend para {file_name}: {str(e)}")
            return {
                "success": False,
                "file_name": file_name,
                "error": str(e),
                "message": f"Error generando código frontend: {str(e)}"
            }
    
    async def generate_backend_only(
        self, 
        analysis_data: Dict[str, Any], 
        file_name: str,
        backend_repo_path: str
    ) -> Dict[str, Any]:
        """Genera solo código backend a partir del análisis de IA"""
        try:
            logger.info(f"Iniciando generación de código backend para {file_name}")
            
            # Validar datos de entrada antes de consumir tokens
            self._validate_analysis_data(analysis_data, file_name)
            self._validate_repository_paths(backend_repo_path, backend_repo_path)  # Usar el mismo path para validación
            
            # Generar código Spring Boot
            logger.info("Generando código Spring Boot...")
            backend_code = await self._generate_backend_code(analysis_data, file_name)
            
            # Crear rama y aplicar cambios
            logger.info("Creando rama y aplicando cambios...")
            branch_name = f"feature/{file_name.replace('.scr', '').lower()}"
            
            # Crear rama en backend
            backend_result = await self._create_branch_and_commit(
                backend_repo_path, 
                branch_name, 
                backend_code, 
                f"feat: Generar entidad backend {file_name.replace('.scr', '')}"
            )
            
            return {
                "success": True,
                "file_name": file_name,
                "backend": {
                    "files_generated": len(backend_code),
                    "branch_created": backend_result["branch_created"],
                    "commit_hash": backend_result["commit_hash"]
                },
                "message": f"Código backend generado exitosamente en rama {branch_name}"
            }
            
        except Exception as e:
            logger.error(f"Error generando código backend para {file_name}: {str(e)}")
            return {
                "success": False,
                "file_name": file_name,
                "error": str(e),
                "message": f"Error generando código backend: {str(e)}"
            }
    
    def _validate_analysis_data(self, analysis_data: Dict[str, Any], file_name: str) -> None:
        """Valida los datos del análisis antes de generar código"""
        if not analysis_data:
            raise ValueError("Los datos del análisis están vacíos")
        
        if not file_name or not file_name.endswith('.scr'):
            raise ValueError(f"Nombre de archivo inválido: {file_name}")
        
        # Validar que existan los campos mínimos necesarios
        required_fields = ['frontend', 'backend']
        for field in required_fields:
            if field not in analysis_data:
                raise ValueError(f"Campo requerido '{field}' no encontrado en el análisis")
        
        logger.info(f"Datos del análisis validados correctamente para {file_name}")
    
    def _validate_repository_paths(self, frontend_repo_path: str, backend_repo_path: str) -> None:
        """Valida que las rutas de los repositorios existan y sean válidas"""
        import os
        
        if not frontend_repo_path or not backend_repo_path:
            raise ValueError("Las rutas de los repositorios no pueden estar vacías")
        
        if not os.path.exists(frontend_repo_path):
            raise ValueError(f"El repositorio frontend no existe en: {frontend_repo_path}")
        
        if not os.path.exists(backend_repo_path):
            raise ValueError(f"El repositorio backend no existe en: {backend_repo_path}")
        
        # Verificar que sean directorios de Git
        if not os.path.exists(os.path.join(frontend_repo_path, '.git')):
            raise ValueError(f"El directorio frontend no es un repositorio Git: {frontend_repo_path}")
        
        if not os.path.exists(os.path.join(backend_repo_path, '.git')):
            raise ValueError(f"El directorio backend no es un repositorio Git: {backend_repo_path}")
        
        logger.info("Rutas de repositorios validadas correctamente")
    
    def _get_unique_branch_name(self, repo_path: str, base_branch_name: str) -> str:
        """Obtiene un nombre único para la rama, agregando sufijo si es necesario"""
        import subprocess
        
        original_cwd = os.getcwd()
        try:
            os.chdir(repo_path)
            
            # Verificar si la rama base existe
            result = subprocess.run(['git', 'branch', '--list', base_branch_name], 
                                  capture_output=True, text=True)
            
            if not result.stdout.strip():
                # La rama no existe, usar el nombre base
                return base_branch_name
            
            # La rama existe, buscar un nombre único
            counter = 1
            while True:
                unique_name = f"{base_branch_name}-{counter}"
                result = subprocess.run(['git', 'branch', '--list', unique_name], 
                                      capture_output=True, text=True)
                
                if not result.stdout.strip():
                    # Encontramos un nombre único
                    logger.info(f"Rama {base_branch_name} ya existe, usando {unique_name}")
                    return unique_name
                
                counter += 1
                
        finally:
            os.chdir(original_cwd)

    async def _create_branch_and_commit(
        self, 
        repo_path: str, 
        branch_name: str, 
        files: Dict[str, str], 
        commit_message: str
    ) -> Dict[str, Any]:
        """Crea una rama, aplica cambios y hace commit"""
        try:
            import subprocess
            import os
            
            # Obtener un nombre único para la rama
            unique_branch_name = self._get_unique_branch_name(repo_path, branch_name)
            
            # Si no hay archivos para crear, solo crear la rama
            if not files:
                logger.info(f"No hay archivos para crear en {repo_path}, solo creando rama {unique_branch_name}")
                original_cwd = os.getcwd()
                os.chdir(repo_path)
                
                try:
                    # Hacer pull para asegurar que tenemos la versión más reciente
                    logger.info(f"Haciendo pull del repositorio {repo_path}")
                    subprocess.run(['git', 'pull', 'origin', 'main'], check=True, capture_output=True)
                    logger.info(f"Pull completado en {repo_path}")
                    
                    # Crear la rama (ya sabemos que es única)
                    subprocess.run(['git', 'checkout', '-b', unique_branch_name], check=True, capture_output=True)
                    logger.info(f"Rama {unique_branch_name} creada en {repo_path}")
                    
                    # Hacer push de la rama vacía
                    subprocess.run(['git', 'push', '-u', 'origin', unique_branch_name], check=True, capture_output=True)
                    logger.info(f"Rama {unique_branch_name} subida al repositorio remoto")
                    
                    return {
                        "success": True,
                        "branch_created": True,
                        "commit_hash": None,
                        "files_created": 0,
                        "message": f"Rama {branch_name} creada y subida sin archivos"
                    }
                finally:
                    os.chdir(original_cwd)
            
            # Cambiar al directorio del repositorio
            original_cwd = os.getcwd()
            os.chdir(repo_path)
            
            try:
                # 0. Hacer pull para asegurar que tenemos la versión más reciente
                logger.info(f"Haciendo pull del repositorio {repo_path}")
                subprocess.run(['git', 'pull', 'origin', 'main'], check=True, capture_output=True)
                logger.info(f"Pull completado en {repo_path}")
                
                # 1. Crear la rama (ya sabemos que es única)
                subprocess.run(['git', 'checkout', '-b', unique_branch_name], check=True, capture_output=True)
                logger.info(f"Rama {unique_branch_name} creada en {repo_path}")
                
                # 2. Crear directorios necesarios y escribir archivos
                for file_path, content in files.items():
                    # Crear directorio si no existe
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    # Escribir archivo
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    logger.info(f"Archivo creado: {file_path}")
                
                # 3. Agregar archivos al staging
                subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
                
                # 4. Hacer commit
                result = subprocess.run(
                    ['git', 'commit', '-m', commit_message], 
                    check=True, 
                    capture_output=True, 
                    text=True
                )
                
                # Extraer hash del commit
                commit_hash = subprocess.run(
                    ['git', 'rev-parse', 'HEAD'], 
                    check=True, 
                    capture_output=True, 
                    text=True
                ).stdout.strip()
                
                # 5. Push de la rama
                subprocess.run(['git', 'push', '-u', 'origin', unique_branch_name], check=True, capture_output=True)
                
                logger.info(f"Commit realizado: {commit_hash}")
                
                return {
                    "branch_created": True,
                    "commit_hash": commit_hash,
                    "files_committed": len(files)
                }
                
            finally:
                # Volver al directorio original
                os.chdir(original_cwd)
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Error en operaciones Git: {e.stderr}")
            raise Exception(f"Error en operaciones Git: {e.stderr}")
        except Exception as e:
            logger.error(f"Error creando rama y commit: {str(e)}")
            raise

