import logging
from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from .domain.entities.configuration import Configuration
from .application.dto.configuration_dto import ConfigurationDTO, CreateConfigurationDTO, UpdateConfigurationDTO
from .infrastructure.repositories.configuration_repository_impl import ConfigurationRepositoryImpl
from .database import get_db, DATABASE_URL
from sqlalchemy.orm import Session
from sqlalchemy import text
from pydantic import BaseModel
from .application.use_cases.test_connections_use_case import TestConnectionsUseCase
from .infrastructure.services.repository_manager_service import RepositoryManagerService
from .infrastructure.services.nsdk_analysis_sync_service import NSDKAnalysisSyncService
from .infrastructure.repositories.nsdk_file_analysis_repository import NSDKFileAnalysisRepository
from pathlib import Path

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),  # Para consola
        logging.FileHandler('backend.log')  # Para archivo
    ]
)

# Log de prueba para verificar que funciona
logger = logging.getLogger(__name__)
logger.info("=== BACKEND INICIADO - LOGGING CONFIGURADO ===")

app = FastAPI(title="Prompt Maestro Backend API")

@app.get("/test-logging", tags=["Test"])
def test_logging():
    """Endpoint de prueba para verificar que el logging funciona"""
    print("=== TEST PRINT ===")
    logger.info("=== TEST LOGGER INFO ===")
    logger.warning("=== TEST LOGGER WARNING ===")
    logger.error("=== TEST LOGGER ERROR ===")
    return {"message": "Logging test completed", "status": "success"}

@app.get("/test-simple", tags=["Test"])
def test_simple():
    """Endpoint de prueba simple"""
    print("=== TEST SIMPLE PRINT ===")
    return {"message": "Simple test works", "status": "success"}

@app.get("/test-db", tags=["Test"])
async def test_database():
    """Endpoint de prueba para verificar conexión a la base de datos"""
    try:
        logger.info("=== PROBANDO CONEXIÓN A BASE DE DATOS ===")
        
        # Probar conexión básica
        db = next(get_db())
        logger.info("[OK] Conexión a BD establecida")
        
        # Probar consulta simple
        result = db.execute(text("SELECT 1 as test"))
        test_value = result.scalar()
        logger.info(f"[OK] Consulta de prueba exitosa: {test_value}")
        
        # Probar tabla de configuraciones
        configs = db.query(Configuration).all()
        logger.info(f"[OK] Tabla de configuraciones accesible: {len(configs)} configuraciones encontradas")
        
        # Probar tabla nsdk_file_analyses específicamente
        try:
            result = db.execute(text("SELECT COUNT(*) FROM nsdk_file_analyses"))
            file_analyses_count = result.scalar()
            logger.info(f"[OK] Tabla nsdk_file_analyses accesible: {file_analyses_count} registros encontrados")
        except Exception as e:
            logger.error(f"[ERROR] Error accediendo a nsdk_file_analyses: {e}")
            file_analyses_count = "ERROR"
        
        # Probar tabla ai_analysis_results específicamente
        try:
            result = db.execute(text("SELECT COUNT(*) FROM ai_analysis_results"))
            ai_results_count = result.scalar()
            logger.info(f"[OK] Tabla ai_analysis_results accesible: {ai_results_count} registros encontrados")
        except Exception as e:
            logger.error(f"[ERROR] Error accediendo a ai_analysis_results: {e}")
            ai_results_count = "ERROR"
        
        db.close()
        return {
            "message": "Conexión a base de datos exitosa",
            "status": "success",
            "configs_count": len(configs),
            "file_analyses_count": file_analyses_count,
            "ai_results_count": ai_results_count,
            "database_url": DATABASE_URL.replace("postgres:postgres", "***:***")  # Ocultar credenciales
        }
        
    except Exception as e:
        logger.error(f"[ERROR] Error en conexión a BD: {e}")
        return {
            "message": f"Error en conexión a base de datos: {str(e)}",
            "status": "error",
            "error": str(e)
        }

@app.get("/test-error", tags=["Test"])
def test_error():
    """Endpoint de prueba que genera un error"""
    print("=== TEST ERROR PRINT ===")
    logger.error("=== TEST ERROR LOGGER ===")
    raise HTTPException(status_code=500, detail="Test error")

# Permitir CORS para desarrollo
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instancia del repositorio
config_repo = ConfigurationRepositoryImpl()

# Instancia del servicio de gestión de repositorios
repo_manager = RepositoryManagerService()

# Instancia del repositorio de análisis de archivos NSDK
def get_analysis_repository():
    db = next(get_db())
    return NSDKFileAnalysisRepository(db)

# Instancia del repositorio de análisis IA
def get_ai_analysis_repository():
    db = next(get_db())
    from .infrastructure.repositories.ai_analysis_repository import AIAnalysisRepository
    return AIAnalysisRepository(db)

# Instancia del repositorio de embeddings vectorizados
def get_vector_embedding_repository(db: Session = Depends(get_db)):
    from .infrastructure.repositories.vector_embedding_repository import VectorEmbeddingRepository
    return VectorEmbeddingRepository(db)

# Instancia del servicio de sincronización de análisis
def get_analysis_sync_service():
    db = next(get_db())
    analysis_repo = NSDKFileAnalysisRepository(db)
    return NSDKAnalysisSyncService(repo_manager, analysis_repo)

# Instancia del servicio de estructura de directorios
def get_directory_tree_service():
    db = next(get_db())
    analysis_repo = NSDKFileAnalysisRepository(db)
    from .infrastructure.repositories.nsdk_directory_repository import NSDKDirectoryRepository
    from .application.services.directory_tree_service import DirectoryTreeService
    directory_repo = NSDKDirectoryRepository(db)
    return DirectoryTreeService(directory_repo, analysis_repo)

# Variable global para el servicio de directorios
directory_tree_service = get_directory_tree_service()

class TestConnectionsRequest(BaseModel):
    config_data: Dict[str, Any]

class TestConnectionsResult(BaseModel):
    service: str
    status: str  # "success" o "error"
    message: str

@app.get("/configurations", response_model=List[ConfigurationDTO], tags=["Configuración"])
async def get_configurations():
    """Listar todas las configuraciones"""
    try:
        configs = await config_repo.find_all()
        return configs
    except Exception as e:
        logger.error(f"Error al obtener configuraciones: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/configurations/active", tags=["Configuración"])
async def get_active_configuration():
    """Obtener la configuración activa"""
    try:
        active_config = await config_repo.find_active()
        if active_config:
            return active_config
        else:
            return {"message": "No hay configuración activa"}
    except Exception as e:
        logger.error(f"Error al obtener configuración activa: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/configurations/{config_id}/set-active", tags=["Configuración"])
async def set_active_configuration(config_id: str):
    """Establecer una configuración como activa"""
    try:
        success = await config_repo.set_active(config_id)
        if success:
            # Reinicializar el servicio LLM con la nueva configuración
            await initialize_llm_service()
            return {"message": f"Configuración {config_id} establecida como activa"}
        else:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al establecer configuración activa: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.get("/configurations/{config_id}", response_model=ConfigurationDTO, tags=["Configuración"])
async def get_configuration(config_id: str):
    """Obtener una configuración por ID"""
    try:
        config = await config_repo.find_by_id(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener configuración {config_id}: {e}")
        raise HTTPException(status_code=500, detail="Error interno del servidor")

@app.post("/configurations", response_model=ConfigurationDTO, tags=["Configuración"])
async def create_configuration(config: CreateConfigurationDTO):
    """Crear una nueva configuración"""
    try:
        logger.info(f"Creando configuración: {config.name}")
        db_config = Configuration(
            name=config.name,
            description=config.description,
            config_data=config.config_data
        )
        saved_config = await config_repo.save(db_config)
        logger.info(f"Configuración creada exitosamente: {saved_config.id}")
        return saved_config
    except Exception as e:
        logger.error(f"Error al crear configuración: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear configuración: {str(e)}")

@app.put("/configurations/{config_id}", response_model=ConfigurationDTO, tags=["Configuración"])
async def update_configuration(config_id: str, config: UpdateConfigurationDTO):
    """Actualizar una configuración"""
    try:
        logger.info(f"Actualizando configuración: {config_id}")
        db_config = await config_repo.find_by_id(config_id)
        if not db_config:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        
        db_config.name = config.name
        db_config.description = config.description
        db_config.config_data = config.config_data
        
        updated_config = await config_repo.update(db_config)
        logger.info(f"Configuración actualizada exitosamente: {config_id}")
        return updated_config
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar configuración {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar configuración: {str(e)}")

@app.delete("/configurations/{config_id}", tags=["Configuración"])
async def delete_configuration(config_id: str):
    """Eliminar una configuración"""
    try:
        logger.info(f"Eliminando configuración: {config_id}")
        success = await config_repo.delete(config_id)
        if not success:
            raise HTTPException(status_code=404, detail="Configuración no encontrada")
        logger.info(f"Configuración eliminada exitosamente: {config_id}")
        return {"deleted": True}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al eliminar configuración {config_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar configuración: {str(e)}")

@app.post("/configurations/{config_id}/activate", tags=["Configuración"])
def activate_configuration(config_id: str):
    """Activar una configuración"""
    return {"activated": True}

@app.post("/configurations/test-connections", response_model=List[TestConnectionsResult], tags=["Configuración"])
async def test_connections(request: TestConnectionsRequest):
    try:
        use_case = TestConnectionsUseCase(repo_manager)
        return use_case.execute(request.config_data)
    except Exception as e:
        logger.error(f"Error al probar conexiones: {e}")
        raise HTTPException(status_code=500, detail=f"Error al probar conexiones: {str(e)}")

# --- ENDPOINTS DE VECTOR STORE Y VECTORIZE ---
from .application.use_cases.vectorization_use_case import VectorizationUseCase
from .infrastructure.services.nsdk_vectorization_service import UnifiedVectorizationService
from .infrastructure.services.vector_store_service_impl import VectorStoreServiceImpl
from .infrastructure.services.llm_service_impl import LLMServiceImpl

# Instanciar servicios
vector_store_service = VectorStoreServiceImpl()
llm_service = LLMServiceImpl()

# Función para inicializar LLM con configuración de BD
async def initialize_llm_service():
    """Inicializa el servicio LLM con la configuración activa de la base de datos"""
    try:
        # Obtener configuración activa
        active_config = await config_repo.find_active()
        if active_config and active_config.config_data.get('llmConfig'):
            llm_config_data = active_config.config_data['llmConfig']
            
            # Crear objeto LLMConfig
            from .domain.entities.configuration import LLMConfig, LLMProvider
            provider_map = {
                'openai': LLMProvider.OPENAI,
                'ollama': LLMProvider.OLLAMA,
                'mistral': LLMProvider.MISTRAL
            }
            
            llm_config = LLMConfig(
                provider=provider_map.get(llm_config_data.get('provider', 'openai'), LLMProvider.OPENAI),
                api_key=llm_config_data.get('apiKey'),
                base_url=llm_config_data.get('baseUrl'),
                model_name=llm_config_data.get('modelName', 'gpt-4'),
                max_tokens=llm_config_data.get('maxTokens', 4096),
                temperature=llm_config_data.get('temperature', 0.7)
            )
            
            # Inicializar LLM service
            await llm_service.initialize(llm_config)
            logger.info(f"LLM service inicializado con proveedor: {llm_config.provider}")
            return True
        else:
            logger.warning("No se encontró configuración LLM activa en la base de datos")
            return False
    except Exception as e:
        logger.error(f"Error inicializando LLM service: {str(e)}")
        return False

unified_vectorization_service = UnifiedVectorizationService(vector_store_service, llm_service, repo_manager, config_repo)
vectorization_use_case = VectorizationUseCase(unified_vectorization_service)

class VectorizeRepositoryRequest(BaseModel):
    config_id: str  # ID de la configuración
    repo_type: str  # Tipo de repositorio: 'source', 'frontend', 'backend'
    branch: str = 'main'

class VectorizeModuleRequest(BaseModel):
    config_id: str  # ID de la configuración
    repo_type: str  # Tipo de repositorio: 'source', 'frontend', 'backend'
    module_path: str
    branch: str = 'main'

class SearchCodeRequest(BaseModel):
    query: str
    limit: int = 10

@app.post("/vectorize/repository", tags=["Vectorización"])
async def vectorize_repository(request: VectorizeRepositoryRequest):
    """Vectorizar un repositorio completo detectando automáticamente su tecnología"""
    print("=== INICIANDO VECTORIZACIÓN DE REPOSITORIO ===")
    print(f"Config ID: {request.config_id}")
    print(f"Repo Type: {request.repo_type}")
    print(f"Branch: {request.branch}")
    
    logger.info(f"=== INICIANDO VECTORIZACIÓN DE REPOSITORIO ===")
    logger.info(f"Config ID: {request.config_id}")
    logger.info(f"Repo Type: {request.repo_type}")
    logger.info(f"Branch: {request.branch}")
    
    try:
        print("Llamando a vectorization_use_case.vectorize_repository...")
        logger.info("Llamando a vectorization_use_case.vectorize_repository...")
        batch = await vectorization_use_case.vectorize_repository(
            config_id=request.config_id,
            repo_type=request.repo_type,
            branch=request.branch
        )
        print(f"Vectorización iniciada exitosamente. Batch ID: {batch.id}")
        logger.info(f"Vectorización iniciada exitosamente. Batch ID: {batch.id}")
        return {
            "status": "started",
            "batch_id": batch.id,
            "batch_name": batch.name,
            "total_files": batch.total_files
        }
    except Exception as e:
        print(f"Error en vectorización: {str(e)}")
        logger.error(f"Error en vectorización: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en vectorización: {str(e)}")

@app.post("/vectorize/all", tags=["Vectorización"])
async def vectorize_all_repositories(request: VectorizeRepositoryRequest):
    """Vectorizar todos los repositorios de una configuración"""
    print("=== INICIANDO VECTORIZACIÓN DE TODOS LOS REPOSITORIOS ===")
    print(f"Config ID: {request.config_id}")
    print(f"Branch: {request.branch}")
    
    logger.info(f"=== INICIANDO VECTORIZACIÓN DE TODOS LOS REPOSITORIOS ===")
    logger.info(f"Config ID: {request.config_id}")
    logger.info(f"Branch: {request.branch}")
    
    try:
        # Primero limpiar TODA la vectorización existente
        await unified_vectorization_service.clear_all_vectorization()
        
        # Vectorizar cada tipo de repositorio
        batches = []
        repo_types = ['source', 'frontend', 'backend']
        
        for repo_type in repo_types:
            try:
                batch = await vectorization_use_case.vectorize_repository(
                    config_id=request.config_id,
                    repo_type=repo_type,
                    branch=request.branch
                )
                batches.append({
                    "repo_type": repo_type,
                    "batch_id": batch.id,
                    "status": "started"
                })
                logger.info(f"Vectorización iniciada para {repo_type}: {batch.id}")
            except Exception as e:
                logger.error(f"Error vectorizando {repo_type}: {str(e)}")
                batches.append({
                    "repo_type": repo_type,
                    "status": "error",
                    "error": str(e)
                })
        
        return {
            "status": "started",
            "message": "Vectorización de todos los repositorios iniciada",
            "batches": batches
        }
        
    except Exception as e:
        print(f"Error en vectorización de todos los repositorios: {str(e)}")
        logger.error(f"Error en vectorización de todos los repositorios: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en vectorización de todos los repositorios: {str(e)}")

@app.post("/vectorize/module", tags=["Vectorización"])
async def vectorize_module(request: VectorizeModuleRequest):
    """Vectorizar un módulo específico"""
    try:
        batch = await vectorization_use_case.vectorize_module(
            config_id=request.config_id,
            repo_type=request.repo_type,
            module_path=request.module_path,
            branch=request.branch
        )
        return {
            "status": "started",
            "batch_id": batch.id,
            "batch_name": batch.name,
            "total_files": batch.total_files
        }
    except Exception as e:
        logger.error(f"Error en vectorización del módulo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en vectorización del módulo: {str(e)}")

@app.get("/vectorize/stats", tags=["Vectorización"])
def get_vectorization_stats():
    """Obtener estadísticas de vectorización"""
    logger.info("=== SOLICITANDO ESTADÍSTICAS DE VECTORIZACIÓN ===")
    try:
        logger.info("Llamando a vectorization_use_case.get_vectorization_stats...")
        stats = vectorization_use_case.get_vectorization_stats()
        logger.info(f"Estadísticas obtenidas: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@app.post("/vectorize/search", tags=["Vectorización"])
async def search_similar_code(request: SearchCodeRequest):
    """Buscar código similar en el vector store"""
    try:
        results = await vectorization_use_case.search_similar_code(
            query=request.query,
            limit=request.limit
        )
        return {
            "query": request.query,
            "results": results,
            "total_results": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")

@app.get("/vectorize/batch/{batch_id}", tags=["Vectorización"])
def get_batch_status(batch_id: str):
    """Obtener estado de un lote de vectorización"""
    try:
        batch_status = vectorization_use_case.get_batch_status(batch_id)
        if batch_status:
            return batch_status
        else:
            raise HTTPException(status_code=404, detail="Lote no encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado del lote: {str(e)}")

@app.post("/vectorize/batch/{batch_id}/cancel", tags=["Vectorización"])
def cancel_batch(batch_id: str):
    """Cancelar un lote de vectorización"""
    try:
        success = vectorization_use_case.cancel_batch(batch_id)
        if success:
            return {"status": "cancelled", "batch_id": batch_id}
        else:
            return {"status": "not_cancelled", "message": "No se pudo cancelar el lote"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cancelando lote: {str(e)}")

# --- ENDPOINTS DE MÓDULOS Y PANTALLAS ---
@app.get("/modules", tags=["Módulos"])
def get_modules():
    """Listar todos los módulos de todos los repositorios"""
    try:
        # Obtener lista de repositorios
        repositories = repo_manager.list_repositories()
        
        all_modules = []
        for repo in repositories:
            repo_name = repo['name']
            modules = repo_manager.get_nsdk_modules(repo_name)
            
            # Agregar información del repositorio a cada módulo
            for module in modules:
                module['repository'] = repo_name
                module['repository_info'] = repo
            
            all_modules.extend(modules)
        
        logger.info(f"Encontrados {len(all_modules)} módulos en total")
        return {
            "total_modules": len(all_modules),
            "modules": all_modules,
            "repositories": repositories
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo módulos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo módulos: {str(e)}")

@app.get("/repository-tree/{repo_name}")
async def get_repository_tree(repo_name: str):
    """Obtener solo la estructura raíz del repositorio para carga lazy"""
    try:
        # Obtener solo la estructura raíz
        root_structure = directory_tree_service.get_root_structure(repo_name)
        return root_structure
    except Exception as e:
        logger.error(f"Error obteniendo estructura raíz del repositorio {repo_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.get("/repository-tree/{repo_name}/directory/{directory_id}")
async def get_directory_contents_by_id(repo_name: str, directory_id: str):
    """Obtener el contenido de un directorio específico por ID"""
    try:
        directory_contents = directory_tree_service.get_directory_contents_by_id(directory_id)
        if directory_contents is None:
            raise HTTPException(status_code=404, detail=f"Directorio {directory_id} no encontrado en {repo_name}")
        
        return directory_contents
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo contenido del directorio {directory_id} en {repo_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

@app.post("/repository-tree/{repo_name}/build")
async def build_repository_tree(repo_name: str):
    """Construir la estructura de directorios en BD para un repositorio"""
    try:
        # Obtener la ruta del repositorio
        repo_path = repo_manager.get_repository_path(repo_name)
        if not repo_path:
            raise HTTPException(status_code=404, detail=f"Repositorio {repo_name} no encontrado")
        
        # Construir el árbol en BD
        root_directory_id = directory_tree_service.build_directory_tree_from_path(str(repo_path), repo_name)
        
        return {
            "message": f"Estructura de directorios construida para {repo_name}",
            "root_directory_id": root_directory_id
        }
    except Exception as e:
        logger.error(f"Error construyendo estructura de directorios para {repo_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")



@app.get("/modules/{module_id}", tags=["Módulos"])
def get_module(module_id: str):
    """Obtener un módulo por ID"""
    return {}

@app.get("/modules/{module_id}/screens", tags=["Módulos"])
def get_module_screens(module_id: str):
    """Listar pantallas de un módulo"""
    return []

# --- ENDPOINTS DE PANTALLAS ---
@app.get("/screens", tags=["Pantallas"])
def get_screens():
    """Listar todas las pantallas de todos los repositorios"""
    try:
        # Obtener lista de repositorios
        repositories = repo_manager.list_repositories()
        
        all_screens = []
        for repo in repositories:
            repo_name = repo['name']
            screens = repo_manager.get_nsdk_screens(repo_name)
            
            # Agregar información del repositorio a cada pantalla
            for screen in screens:
                screen['repository'] = repo_name
                screen['repository_info'] = repo
            
            all_screens.extend(screens)
        
        logger.info(f"Encontradas {len(all_screens)} pantallas en total")
        return {
            "total_screens": len(all_screens),
            "screens": all_screens,
            "repositories": repositories
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo pantallas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo pantallas: {str(e)}")

@app.get("/screens/{screen_id}", tags=["Pantallas"])
def get_screen(screen_id: str):
    """Obtener una pantalla por ID"""
    return {}

# --- ENDPOINTS DE ANÁLISIS ---
@app.get("/analysis", tags=["Análisis"])
def get_analyses():
    """Listar todos los análisis"""
    return []

@app.get("/analysis/{analysis_id}", tags=["Análisis"])
def get_analysis(analysis_id: str):
    """Obtener un análisis por ID"""
    return {}

# --- ENDPOINTS DE LLM Y CHAT ---
@app.post("/llm/chat", tags=["LLM"])
def chat_completion():
    """Realizar una completación de chat con LLM"""
    return {"response": "OK"}

@app.post("/llm/embedding", tags=["LLM"])
def get_embedding():
    """Obtener embedding de un texto"""
    return {"embedding": []} 

@app.post("/repositories/{repo_name}/sync-analysis", tags=["Análisis NSDK"])
def sync_repository_analysis(
    repo_name: str, 
    force_resync: bool = False,
    analysis_sync_service: NSDKAnalysisSyncService = Depends(get_analysis_sync_service)
):
    """Sincroniza el análisis de archivos NSDK de un repositorio con la base de datos"""
    try:
        sync_stats = analysis_sync_service.sync_repository_analysis(repo_name, force_resync)
        logger.info(f"Sincronización de análisis completada para {repo_name}: {sync_stats}")
        return {
            "repository_name": repo_name,
            "sync_stats": sync_stats,
            "message": "Sincronización de análisis completada exitosamente"
        }
    except Exception as e:
        logger.error(f"Error en sincronización de análisis para {repo_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en sincronización: {str(e)}")

@app.get("/repositories/{repo_name}/analysis-status", tags=["Análisis NSDK"])
def get_repository_analysis_status(
    repo_name: str,
    analysis_sync_service: NSDKAnalysisSyncService = Depends(get_analysis_sync_service)
):
    """Obtiene el estado del análisis de un repositorio"""
    try:
        status = analysis_sync_service.get_repository_analysis_status(repo_name)
        return status
    except Exception as e:
        logger.error(f"Error obteniendo estado de análisis para {repo_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")

@app.get("/repositories/{repo_name}/file-content", tags=["Archivos"])
def get_file_content(
    repo_name: str,
    file_id: Optional[str] = None,
    file_path: Optional[str] = None,
    analysis_repo: NSDKFileAnalysisRepository = Depends(get_analysis_repository)
):
    """Devuelve el contenido de un fichero del repositorio, por id de análisis o por path absoluto.
    Si se proporciona file_id, se obtiene el path desde la BD. Si se proporciona file_path, se usa directamente.
    """
    try:
        # Determinar ruta del repositorio y del fichero
        repo_path = repo_manager.get_repository_path(repo_name)
        if not repo_path:
            raise HTTPException(status_code=404, detail=f"Repositorio {repo_name} no encontrado")

        resolved_repo = Path(repo_path).resolve()

        target_path: Optional[Path] = None

        if file_id:
            analysis = analysis_repo.get_by_id(file_id)
            if not analysis:
                raise HTTPException(status_code=404, detail=f"Archivo con id {file_id} no encontrado en BD")
            candidate = Path(analysis.file_path)
            target_path = candidate.resolve()
        elif file_path:
            candidate = Path(file_path)
            target_path = candidate.resolve()
        else:
            raise HTTPException(status_code=400, detail="Debe proporcionar file_id o file_path")

        # Seguridad: asegurar que el fichero está dentro del repo
        if not str(target_path).startswith(str(resolved_repo)):
            # Intentar resolver como ruta relativa al repo
            candidate_rel = (resolved_repo / target_path.name).resolve()
            if not str(candidate_rel).startswith(str(resolved_repo)):
                raise HTTPException(status_code=400, detail="Ruta fuera del repositorio")
            target_path = candidate_rel

        if not target_path.exists() or not target_path.is_file():
            raise HTTPException(status_code=404, detail="Fichero no encontrado")

        # Leer contenido como texto (UTF-8), ignorando errores
        try:
            content_text = target_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            # Si no se puede como texto, devolver vacío y tamaño
            content_text = ""

        size_bytes = target_path.stat().st_size

        return {
            "repository": repo_name,
            "path": str(target_path),
            "size_bytes": size_bytes,
            "content_text": content_text,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error leyendo contenido de fichero en {repo_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error leyendo fichero: {str(e)}")

@app.get("/repositories/{repo_name}/analysis", tags=["Análisis NSDK"])
def get_repository_analysis(
    repo_name: str,
    file_type: Optional[str] = None,
    status: Optional[str] = None,
    analysis_repo: NSDKFileAnalysisRepository = Depends(get_analysis_repository)
):
    """Obtiene los análisis de archivos NSDK de un repositorio"""
    try:
        if file_type and status:
            analyses = analysis_repo.get_by_type_and_status(file_type, status, repo_name)
        elif file_type:
            analyses = analysis_repo.get_by_type(file_type, repo_name)
        elif status:
            analyses = analysis_repo.get_by_status(status, repo_name)
        else:
            analyses = analysis_repo.get_by_repository(repo_name)
        
        return {
            "repository_name": repo_name,
            "total_analyses": len(analyses),
            "analyses": [analysis.__dict__ for analysis in analyses]
        }
    except Exception as e:
        logger.error(f"Error obteniendo análisis para {repo_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo análisis: {str(e)}")

@app.get("/repositories/{repo_name}/analysis/{analysis_id}", tags=["Análisis NSDK"])
def get_analysis_by_id(
    repo_name: str,
    analysis_id: str,
    analysis_repo: NSDKFileAnalysisRepository = Depends(get_analysis_repository)
):
    """Obtiene un análisis específico por ID"""
    try:
        analysis = analysis_repo.get_by_id(analysis_id)
        if not analysis:
            raise HTTPException(status_code=404, detail="Análisis no encontrado")
        
        return analysis.__dict__
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo análisis {analysis_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo análisis: {str(e)}")

@app.post("/repositories/{repo_name}/cleanup-orphaned", tags=["Análisis NSDK"])
def cleanup_orphaned_analyses(
    repo_name: str,
    analysis_sync_service: NSDKAnalysisSyncService = Depends(get_analysis_sync_service)
):
    """Limpia análisis huérfanos de un repositorio"""
    try:
        cleanup_stats = analysis_sync_service.cleanup_orphaned_analyses(repo_name)
        logger.info(f"Limpieza de análisis huérfanos completada para {repo_name}: {cleanup_stats}")
        return {
            "repository_name": repo_name,
            "cleanup_stats": cleanup_stats,
            "message": "Limpieza de análisis huérfanos completada exitosamente"
        }
    except Exception as e:
        logger.error(f"Error en limpieza de análisis huérfanos para {repo_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en limpieza: {str(e)}")

@app.post("/repositories/{repo_name}/files/{file_id}/analyze-ai", tags=["Análisis IA"])
async def analyze_file_with_ai(
    repo_name: str,
    file_id: str,
    analysis_repo: NSDKFileAnalysisRepository = Depends(get_analysis_repository),
    ai_analysis_repo = Depends(get_ai_analysis_repository),
    db: Session = Depends(get_db)
):
    """Analiza un fichero .SCR con IA para migración a Angular/Spring Boot"""
    try:
        # Obtener el fichero de la BD
        file_analysis = analysis_repo.get_by_id(file_id)
        if not file_analysis:
            raise HTTPException(status_code=404, detail=f"Fichero {file_id} no encontrado")
        
        # Verificar que es un fichero .SCR
        if not file_analysis.file_name.upper().endswith('.SCR'):
            raise HTTPException(status_code=400, detail="Solo se pueden analizar ficheros .SCR")
        
        # Verificar que el fichero existe en disco
        file_path = Path(file_analysis.file_path)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="Fichero no encontrado en disco")
        
        # Leer contenido del fichero
        try:
            file_content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error leyendo fichero: {str(e)}")
        
        # Marcar como analizando
        file_analysis.analysis_status = "analyzing"
        analysis_repo.update(file_analysis)
        
        logger.info(f"Iniciando análisis IA para {file_analysis.file_name}")
        
        # Inicializar LLM service con configuración de BD
        await initialize_llm_service()
        
        # Importar y usar el servicio de análisis IA
        from .application.services.ai_analysis_service import AIAnalysisService
        from .application.services.nsdk_query_service import NSDKQueryService
        
        # Crear instancia del servicio de consulta NSDK
        nsdk_query_service = NSDKQueryService(db)
        
        # Crear instancia del servicio de análisis IA con todos los servicios
        ai_service = AIAnalysisService(vectorization_use_case, llm_service, nsdk_query_service)
        
        try:
            # Realizar análisis con IA
            analysis_result = await ai_service.analyze_scr_file(
                file_path=str(file_path),
                file_content=file_content,
                file_name=file_analysis.file_name
            )
            
            # Guardar resultado del análisis en BD
            from .domain.entities.ai_analysis_result import AIAnalysisResult
            
            ai_result = AIAnalysisResult(
                file_analysis_id=file_id,
                analysis_data=analysis_result,
                raw_response=str(analysis_result)
            )
            
            saved_ai_result = ai_analysis_repo.create(ai_result)
            
            # Actualizar estado en BD
            file_analysis.analysis_status = "analyzed"
            analysis_repo.update(file_analysis)
            
            logger.info(f"Análisis IA completado y guardado para {file_analysis.file_name}")
            
            return {
                "file_id": file_id,
                "file_name": file_analysis.file_name,
                "status": "analyzed",
                "message": f"Análisis IA completado para {file_analysis.file_name}",
                "analysis_result": analysis_result,
                "analysis_id": saved_ai_result.id,
                "content_length": len(file_content)
            }
            
        except Exception as ai_error:
            logger.error(f"Error en análisis IA: {str(ai_error)}")
            
            # Marcar como error en BD
            file_analysis.analysis_status = "error"
            analysis_repo.update(file_analysis)
            
            raise HTTPException(
                status_code=500, 
                detail=f"Error en análisis IA: {str(ai_error)}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error en análisis IA para {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en análisis IA: {str(e)}")

@app.get("/repositories/{repo_name}/files/{file_id}/ai-analysis", tags=["Análisis IA"])
def get_ai_analysis_result(
    repo_name: str,
    file_id: str,
    ai_analysis_repo = Depends(get_ai_analysis_repository)
):
    """Obtiene el resultado del análisis IA más reciente para un fichero"""
    try:
        logger.info(f"Buscando análisis IA para file_id: {file_id}")
        ai_result = ai_analysis_repo.get_by_file_analysis_id(file_id)
        
        if not ai_result:
            logger.warning(f"No se encontró análisis IA para file_id: {file_id}")
            raise HTTPException(status_code=404, detail="No se encontró análisis IA para este fichero")
        
        logger.info(f"Análisis IA encontrado: {ai_result.id} para file_id: {file_id}")
        analysis_dict = ai_result.to_dict()
        logger.info(f"Análisis convertido a dict: {list(analysis_dict.keys())}")
        
        return {
            "file_id": file_id,
            "analysis": analysis_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo análisis IA para {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo análisis IA: {str(e)}")

@app.post("/repositories/{repo_name}/files/{file_id}/ai-analysis", tags=["Análisis IA"])
async def execute_ai_analysis(
    repo_name: str,
    file_id: str,
    db: Session = Depends(get_db)
):
    """Ejecuta un nuevo análisis IA para un fichero con documentación NSDK"""
    try:
        logger.info(f"Ejecutando análisis IA para file_id: {file_id}")
        
        # Obtener información del archivo
        from .infrastructure.repositories.nsdk_file_analysis_repository import NSDKFileAnalysisRepository
        file_analysis_repo = NSDKFileAnalysisRepository(db)
        file_analysis = file_analysis_repo.get_by_id(file_id)
        
        if not file_analysis:
            raise HTTPException(status_code=404, detail="Archivo no encontrado")
        
        # Leer contenido del archivo
        file_path = file_analysis.file_path
        try:
            # Intentar diferentes codificaciones
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            file_content = None
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        file_content = f.read()
                    logger.info(f"Archivo leído con codificación: {encoding}")
                    break
                except UnicodeDecodeError:
                    continue
            
            if file_content is None:
                raise Exception("No se pudo leer el archivo con ninguna codificación soportada")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error leyendo archivo: {str(e)}")
        
        # Consultar documentación NSDK para contexto
        from .application.services.nsdk_query_service import NSDKQueryService
        nsdk_query_service = NSDKQueryService(db)
        
        # Extraer términos técnicos del archivo
        import re
        technical_terms = []
        patterns = [
            r'DEFINE\s+(\w+)',  # Definiciones
            r'CALL\s+(\w+)',    # Llamadas a funciones
            r'USE\s+(\w+)',     # Uso de módulos
            r'(\w+)\s*\(',      # Funciones
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, file_content, re.IGNORECASE)
            technical_terms.extend(matches)
        
        # Consultar documentación para términos específicos
        nsdk_context = ""
        for term in technical_terms[:3]:  # Limitar a 3 consultas
            try:
                result = await nsdk_query_service.query_documentation(term)
                if result and "Información encontrada" in result:
                    nsdk_context += f"\n**{term}:** {result}\n"
            except Exception as e:
                logger.warning(f"Error consultando documentación para '{term}': {e}")
                continue
        
        # Crear prompt mejorado con documentación NSDK
        enhanced_prompt = f"""
# ANÁLISIS DE MIGRACIÓN DE FICHERO .SCR A ANGULAR/SPRING BOOT

## FICHERO A ANALIZAR:
**Nombre:** {file_analysis.file_name}

**Contenido del fichero .SCR:**
```
{file_content[:2000]}{"..." if len(file_content) > 2000 else ""}
```

## DOCUMENTACIÓN TÉCNICA NSDK:
{nsdk_context if nsdk_context else "No se encontró documentación específica para los términos técnicos del archivo."}

## INSTRUCCIONES:
Analiza este fichero .SCR y proporciona un análisis detallado para su migración a:
- **Frontend:** Angular con Angular Material
- **Backend:** Java Spring Boot con JPA/Hibernate

**IMPORTANTE:** Presta especial atención a:
1. **Menú Superior:** Identifica el menú de navegación principal
2. **Tablas:** Identifica TODAS las tablas, sus columnas y funcionalidades
3. **Navegaciones:** Identifica todas las navegaciones entre pantallas
4. **Controles:** Identifica todos los controles y sus propiedades

Responde en formato JSON válido con la siguiente estructura:
```json
{{
    "analysis_summary": "Resumen del análisis",
    "file_type": "screen|form|report|utility",
    "complexity": "low|medium|high",
    "estimated_hours": 40,
    "frontend": {{
        "component_type": "form|table|navigation",
        "fields": [],
        "tables": [],
        "buttons": [],
        "navigation": []
    }},
    "backend": {{
        "entities": [],
        "services": [],
        "controllers": []
    }},
    "migration_notes": "Notas importantes para la migración",
    "potential_issues": ["Lista de problemas potenciales"]
}}
```
"""
        
        # Enviar a OpenAI
        from .infrastructure.services.llm_service_impl import LLMServiceImpl
        llm_service = LLMServiceImpl()
        
        system_prompt = """Eres un experto en migración de aplicaciones NS-DK a Angular/Spring Boot. 
Analiza ficheros .SCR y proporciona un análisis detallado para su migración a tecnologías modernas.
Responde SIEMPRE en formato JSON válido."""
        
        ai_response = await llm_service.chat_completion([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": enhanced_prompt}
        ])
        
        # Procesar respuesta
        import json
        try:
            analysis_result = json.loads(ai_response)
        except json.JSONDecodeError:
            # Si no es JSON válido, crear un resultado básico
            analysis_result = {
                "analysis_summary": "Análisis completado con documentación NSDK",
                "file_type": "screen",
                "complexity": "medium",
                "estimated_hours": 40,
                "frontend": {"component_type": "form", "fields": [], "tables": [], "buttons": [], "navigation": []},
                "backend": {"entities": [], "services": [], "controllers": []},
                "migration_notes": "Análisis realizado con contexto de documentación NSDK",
                "potential_issues": []
            }
        
        # Guardar resultado en BD
        from .infrastructure.repositories.ai_analysis_repository import AIAnalysisRepository
        from .domain.entities.ai_analysis_result import AIAnalysisResult
        
        ai_analysis_repo = AIAnalysisRepository(db)
        
        analysis_data = {
            'analysis_summary': analysis_result.get('analysis_summary', ''),
            'file_type': analysis_result.get('file_type', ''),
            'complexity': analysis_result.get('complexity', ''),
            'estimated_hours': analysis_result.get('estimated_hours', 0),
            'frontend': analysis_result.get('frontend', {}),
            'backend': analysis_result.get('backend', {}),
            'migration_notes': analysis_result.get('migration_notes', ''),
            'potential_issues': analysis_result.get('potential_issues', []),
            'analysis_version': '2.0'  # Nueva versión con documentación NSDK
        }
        
        ai_result = AIAnalysisResult(
            file_analysis_id=file_id,
            analysis_data=analysis_data,
            raw_response=ai_response
        )
        
        saved_result = ai_analysis_repo.create(ai_result)
        
        logger.info(f"Análisis IA completado y guardado: {saved_result.id}")
        
        return {
            "status": "success",
            "message": "Análisis IA completado exitosamente con documentación NSDK",
            "analysis_id": saved_result.id,
            "file_id": file_id,
            "analysis": saved_result.to_dict(),
            "nsdk_context_used": bool(nsdk_context)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error ejecutando análisis IA para {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error ejecutando análisis IA: {str(e)}")

@app.get("/ai-analysis/statistics", tags=["Análisis IA"])
def get_ai_analysis_statistics(
    ai_analysis_repo = Depends(get_ai_analysis_repository)
):
    """Obtiene estadísticas de los análisis IA realizados"""
    try:
        stats = ai_analysis_repo.get_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de análisis IA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@app.get("/ai-analysis/debug", tags=["Análisis IA"])
def debug_ai_analysis(
    ai_analysis_repo = Depends(get_ai_analysis_repository)
):
    """Endpoint de debug para verificar análisis IA en BD"""
    try:
        # Obtener todos los análisis
        all_analyses = ai_analysis_repo.get_all()
        
        debug_info = {
            "total_analyses": len(all_analyses),
            "analyses": []
        }
        
        for analysis in all_analyses:
            debug_info["analyses"].append({
                "id": analysis.id,
                "file_analysis_id": analysis.file_analysis_id,
                "file_type": analysis.file_type,
                "complexity": analysis.complexity,
                "created_at": analysis.created_at.isoformat() if analysis.created_at else None,
                "has_frontend": bool(analysis.frontend_analysis),
                "has_backend": bool(analysis.backend_analysis)
            })
        
        return debug_info
    except Exception as e:
        logger.error(f"Error en debug de análisis IA: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en debug: {str(e)}") 

@app.get("/vectorize/embeddings/stats", tags=["Vectorización"])
def get_embeddings_stats(
    vector_embedding_repo = Depends(get_vector_embedding_repository)
):
    """Obtener estadísticas de embeddings vectorizados"""
    try:
        stats = vector_embedding_repo.get_stats()
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas de embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

@app.delete("/vectorize/embeddings/clear", tags=["Vectorización"])
def clear_embeddings(
    config_id: str = None,
    repo_type: str = None,
    branch: str = 'main',
    vector_embedding_repo = Depends(get_vector_embedding_repository)
):
    """Limpiar embeddings vectorizados"""
    try:
        if config_id and repo_type:
            # Limpiar embeddings específicos
            success = vector_embedding_repo.delete_by_config_and_repo(config_id, repo_type, branch)
            message = f"Embeddings eliminados para config_id: {config_id}, repo_type: {repo_type}, branch: {branch}"
        elif config_id:
            # Limpiar todos los embeddings de una configuración
            success = vector_embedding_repo.delete_by_config(config_id)
            message = f"Todos los embeddings eliminados para config_id: {config_id}"
        else:
            raise HTTPException(status_code=400, detail="Debe especificar al menos config_id")
        
        if success:
            return {
                "status": "success",
                "message": message
            }
        else:
            raise HTTPException(status_code=500, detail="Error eliminando embeddings")
            
    except Exception as e:
        logger.error(f"Error limpiando embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error limpiando embeddings: {str(e)}") 

# Función para inicializar embeddings al arrancar
async def initialize_embeddings_on_startup():
    """Inicializa embeddings desde BD al Vector Store al arrancar"""
    try:
        logger.info("=== INICIALIZANDO EMBEDDINGS AL ARRANCAR ===")
        
        from .infrastructure.services.embedding_sync_service import EmbeddingSyncService
        from .infrastructure.repositories.vector_embedding_repository import VectorEmbeddingRepository
        from .database import get_db
        
        # Obtener repositorio de embeddings
        db = next(get_db())
        vector_embedding_repo = VectorEmbeddingRepository(db)
        
        # Verificar si hay embeddings en la BD
        stats = vector_embedding_repo.get_stats()
        if stats.get('total_embeddings', 0) == 0:
            logger.info("=== NO HAY EMBEDDINGS EN BD - OMITIENDO INICIALIZACIÓN ===")
            return
        
        # Crear servicio de sincronización
        sync_service = EmbeddingSyncService(vector_store_service)
        
        # Cargar embeddings desde BD
        success = await sync_service.load_embeddings_from_db(vector_embedding_repo)
        
        if success:
            logger.info("=== EMBEDDINGS INICIALIZADOS EXITOSAMENTE ===")
        else:
            logger.warning("=== ADVERTENCIA: No se pudieron inicializar embeddings ===")
            
    except Exception as e:
        logger.error(f"Error inicializando embeddings al arrancar: {str(e)}")

@app.post("/vectorize/embeddings/sync", tags=["Vectorización"])
async def sync_embeddings_to_vector_store(
    config_id: str = None,
    vector_embedding_repo = Depends(get_vector_embedding_repository)
):
    """Sincronizar embeddings desde BD al Vector Store"""
    try:
        from .infrastructure.services.embedding_sync_service import EmbeddingSyncService
        
        sync_service = EmbeddingSyncService(vector_store_service)
        success = await sync_service.sync_embeddings_to_vector_store(
            vector_embedding_repo, 
            config_id=config_id
        )
        
        if success:
            return {
                "status": "success",
                "message": "Embeddings sincronizados al Vector Store exitosamente"
            }
        else:
            raise HTTPException(status_code=500, detail="Error sincronizando embeddings")
            
    except Exception as e:
        logger.error(f"Error sincronizando embeddings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error sincronizando embeddings: {str(e)}")

@app.get("/vectorize/vector-store/stats", tags=["Vectorización"])
def get_vector_store_stats():
    """Obtener estadísticas del Vector Store"""
    try:
        from .infrastructure.services.embedding_sync_service import EmbeddingSyncService
        
        sync_service = EmbeddingSyncService(vector_store_service)
        stats = sync_service.get_vector_store_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas del Vector Store: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")

# Evento de inicio de la aplicación
@app.on_event("startup")
async def startup_event():
    """Evento que se ejecuta al arrancar la aplicación"""
    logger.info("=== INICIANDO APLICACIÓN ===")
    
    # Inicializar LLM service
    await initialize_llm_service()
    
    # Inicializar embeddings
    await initialize_embeddings_on_startup()
    
    logger.info("=== APLICACIÓN INICIADA EXITOSAMENTE ===") 

@app.post("/test/search", tags=["Test"])
async def test_semantic_search(
    query: str,
    limit: int = 5,
    threshold: float = 0.5,
    vector_embedding_repo = Depends(get_vector_embedding_repository)
):
    """Endpoint temporal para probar búsquedas semánticas"""
    try:
        from .application.use_cases.vectorization_use_case import VectorizationUseCase
        from .infrastructure.services.llm_service_impl import LLMServiceImpl
        
        # Crear LLM service para obtener embedding de la query
        llm_service = LLMServiceImpl()
        
        # Obtener embedding de la query
        logger.info(f"Obteniendo embedding para query: {query}")
        query_embedding = await llm_service.get_embedding(query)
        logger.info(f"Embedding obtenido, longitud: {len(query_embedding)}")
        
        # Buscar similares
        config = {
            'type': 'faiss',
            'collectionName': 'nsdk-embeddings'
        }
        
        results = vector_store_service.search_similar(
            query_embedding=query_embedding,
            config=config,
            limit=limit,
            threshold=threshold
        )
        
        return {
            "status": "success",
            "query": query,
            "results_count": len(results),
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Error en búsqueda de prueba: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error en búsqueda: {str(e)}")


# ===== ENDPOINTS PARA SISTEMA DE DOCUMENTACIÓN NSDK =====

@app.post("/nsdk-documents/upload", tags=["NSDK Documentation"])
async def upload_nsdk_document(
    file_path: str = Body(..., description="Ruta del archivo PDF"),
    document_name: str = Body(..., description="Nombre del documento"),
    db: Session = Depends(get_db)
):
    """Sube y procesa un documento PDF de NSDK"""
    try:
        from .application.services.nsdk_pdf_processor import NSDKPDFProcessor
        
        processor = NSDKPDFProcessor(db)
        document_id = await processor.process_nsdk_document(file_path, document_name)
        
        return {
            "status": "success",
            "message": "Documento procesado exitosamente",
            "document_id": document_id,
            "document_name": document_name
        }
        
    except Exception as e:
        logger.error(f"Error procesando documento NSDK: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")


@app.post("/nsdk-documents/process-existing", tags=["NSDK Documentation"])
async def process_existing_nsdk_document(
    document_name: str = Body(..., description="Nombre del documento a procesar"),
    db: Session = Depends(get_db)
):
    """Procesa un documento PDF existente en la carpeta NSDK-DOCS"""
    try:
        import os
        from .application.services.nsdk_pdf_processor import NSDKPDFProcessor
        
        # Buscar el archivo en la carpeta NSDK-DOCS
        nsdk_docs_path = "../NSDK-DOCS"
        if not os.path.exists(nsdk_docs_path):
            raise HTTPException(status_code=404, detail="Carpeta NSDK-DOCS no encontrada")
        
        # Buscar archivo PDF
        pdf_file = None
        for file in os.listdir(nsdk_docs_path):
            if file.lower().endswith('.pdf') and document_name.lower() in file.lower():
                pdf_file = os.path.join(nsdk_docs_path, file)
                break
        
        if not pdf_file:
            raise HTTPException(status_code=404, detail=f"Archivo PDF con nombre '{document_name}' no encontrado")
        
        processor = NSDKPDFProcessor(db)
        document_id = await processor.process_nsdk_document(pdf_file, document_name)
        
        return {
            "status": "success",
            "message": "Documento procesado exitosamente",
            "document_id": document_id,
            "document_name": document_name,
            "file_path": pdf_file
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error procesando documento NSDK existente: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando documento: {str(e)}")


@app.get("/nsdk-documents/{document_id}/status", tags=["NSDK Documentation"])
async def get_document_status(document_id: str, db: Session = Depends(get_db)):
    """Obtiene el estado de procesamiento de un documento"""
    try:
        from .application.services.nsdk_pdf_processor import NSDKPDFProcessor
        
        processor = NSDKPDFProcessor(db)
        status = await processor.get_document_status(document_id)
        
        if status:
            return {
                "status": "success",
                "document": status
            }
        else:
            raise HTTPException(status_code=404, detail="Documento no encontrado")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estado del documento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado: {str(e)}")


@app.get("/nsdk-documents", tags=["NSDK Documentation"])
async def get_all_documents(db: Session = Depends(get_db)):
    """Obtiene todos los documentos NSDK procesados"""
    try:
        from .infrastructure.repositories.nsdk_document_repository import NSDKDocumentRepository
        
        repo = NSDKDocumentRepository(db)
        documents = await repo.get_all()
        
        return {
            "status": "success",
            "documents": [doc.to_dict() for doc in documents]
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo documentos: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo documentos: {str(e)}")


@app.post("/nsdk-documents/query", tags=["NSDK Documentation"])
async def query_nsdk_documentation(
    query: str = Body(..., description="Consulta sobre documentación NSDK"),
    context: str = Body("", description="Contexto adicional"),
    db: Session = Depends(get_db)
):
    """Consulta la documentación NSDK"""
    try:
        from .application.services.nsdk_query_service import NSDKQueryService
        
        query_service = NSDKQueryService(db)
        result = await query_service.query_documentation(query, context)
        
        return {
            "status": "success",
            "query": query,
            "result": result
        }
        
    except Exception as e:
        logger.error(f"Error consultando documentación: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error consultando documentación: {str(e)}")


@app.get("/nsdk-documents/stats", tags=["NSDK Documentation"])
async def get_documentation_stats(db: Session = Depends(get_db)):
    """Obtiene estadísticas de la documentación NSDK"""
    try:
        from .application.services.nsdk_query_service import NSDKQueryService
        
        query_service = NSDKQueryService(db)
        stats = await query_service.get_documentation_stats()
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


@app.post("/nsdk-documents/test-indexing", tags=["NSDK Documentation"])
async def test_document_indexing(db: Session = Depends(get_db)):
    """Prueba la indexación de documentos NSDK"""
    try:
        from .application.services.nsdk_query_service import NSDKQueryService
        
        query_service = NSDKQueryService(db)
        results = await query_service.test_document_indexing()
        
        return {
            "status": "success",
            "test_results": results
        }
        
    except Exception as e:
        logger.error(f"Error probando indexación: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error probando indexación: {str(e)}")


@app.get("/nsdk-documents/available", tags=["NSDK Documentation"])
async def get_available_nsdk_documents():
    """Obtiene la lista de documentos PDF disponibles en NSDK-DOCS"""
    try:
        import os
        
        nsdk_docs_path = "../NSDK-DOCS"
        if not os.path.exists(nsdk_docs_path):
            return {
                "status": "success",
                "documents": [],
                "message": "Carpeta NSDK-DOCS no encontrada"
            }
        
        pdf_files = []
        for file in os.listdir(nsdk_docs_path):
            if file.lower().endswith('.pdf'):
                file_path = os.path.join(nsdk_docs_path, file)
                file_size = os.path.getsize(file_path)
                pdf_files.append({
                    "name": file,
                    "display_name": file.replace('.pdf', '').replace('_', ' ').title(),
                    "size_mb": round(file_size / (1024 * 1024), 2),
                    "path": file_path
                })
        
        # Ordenar por nombre
        pdf_files.sort(key=lambda x: x['name'])
        
        return {
            "status": "success",
            "documents": pdf_files,
            "total_count": len(pdf_files)
        }
        
    except Exception as e:
        logger.error(f"Error obteniendo documentos disponibles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error obteniendo documentos: {str(e)}")

@app.post("/test/ai-analysis-with-vectorization", tags=["Test"])
async def test_ai_analysis_with_vectorization(
    query: str = Body(..., description="Consulta de prueba para búsqueda vectorizada"),
    db: Session = Depends(get_db)
):
    """Endpoint de prueba para verificar la integración de vectorización en análisis IA"""
    try:
        logger.info(f"=== PRUEBA DE INTEGRACIÓN VECTORIZACIÓN + ANÁLISIS IA ===")
        logger.info(f"Query de prueba: {query}")
        
        # 1. Probar búsqueda de código similar
        logger.info("1. Probando búsqueda de código similar...")
        similar_results = await vectorization_use_case.search_similar_code(
            query=query,
            limit=3
        )
        logger.info(f"Resultados de búsqueda similar: {len(similar_results)}")
        
        # 2. Probar consulta de documentación NSDK
        logger.info("2. Probando consulta de documentación NSDK...")
        from .application.services.nsdk_query_service import NSDKQueryService
        nsdk_query_service = NSDKQueryService(db)
        nsdk_context = await nsdk_query_service.query_documentation(query)
        logger.info(f"Contexto NSDK obtenido: {len(nsdk_context)} caracteres")
        
        # 3. Probar creación del servicio de análisis IA
        logger.info("3. Probando creación del servicio de análisis IA...")
        from .application.services.ai_analysis_service import AIAnalysisService
        ai_service = AIAnalysisService(vectorization_use_case, llm_service, nsdk_query_service)
        logger.info("Servicio de análisis IA creado exitosamente")
        
        # 4. Simular análisis con contexto vectorizado
        logger.info("4. Simulando análisis con contexto vectorizado...")
        test_content = f"SCREEN TEST_SCREEN\nFIELD test_field\nBUTTON test_button\n{query}"
        
        # Obtener contexto similar
        similar_context = await ai_service._get_similar_code_context(test_content)
        logger.info(f"Contexto similar obtenido: {len(similar_context)} elementos")
        
        # Obtener contexto NSDK
        nsdk_context_result = await ai_service._get_nsdk_documentation_context(test_content)
        logger.info(f"Contexto NSDK obtenido: {len(nsdk_context_result)} caracteres")
        
        return {
            "status": "success",
            "message": "Integración vectorización + análisis IA funcionando correctamente",
            "test_results": {
                "similar_code_search": {
                    "query": query,
                    "results_count": len(similar_results),
                    "results": similar_results[:2] if similar_results else []  # Solo primeros 2
                },
                "nsdk_documentation": {
                    "query": query,
                    "context_length": len(nsdk_context),
                    "has_content": "Información encontrada" in nsdk_context
                },
                "ai_service_integration": {
                    "service_created": True,
                    "similar_context_count": len(similar_context),
                    "nsdk_context_length": len(nsdk_context_result)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error en prueba de integración: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error en prueba: {str(e)}")

@app.post("/test/ai-analysis-detailed", tags=["Test"])
async def test_ai_analysis_detailed(
    file_content: str = Body(..., description="Contenido del archivo .SCR para análisis detallado"),
    file_name: str = Body("test_file.scr", description="Nombre del archivo"),
    db: Session = Depends(get_db)
):
    """Endpoint de prueba para análisis IA detallado con logs completos"""
    try:
        logger.info(f"=== ANÁLISIS IA DETALLADO CON LOGS COMPLETOS ===")
        logger.info(f"Archivo: {file_name}")
        logger.info(f"Contenido: {len(file_content)} caracteres")
        
        # Crear servicios
        from .application.services.ai_analysis_service import AIAnalysisService
        from .application.services.nsdk_query_service import NSDKQueryService
        
        nsdk_query_service = NSDKQueryService(db)
        ai_service = AIAnalysisService(vectorization_use_case, llm_service, nsdk_query_service)
        
        # Realizar análisis completo con logs detallados
        logger.info("Iniciando análisis IA completo...")
        analysis_result = await ai_service.analyze_scr_file(
            file_path=f"/test/{file_name}",
            file_content=file_content,
            file_name=file_name
        )
        
        logger.info("=== ANÁLISIS COMPLETADO ===")
        logger.info(f"Resultado: {analysis_result}")
        
        return {
            "status": "success",
            "message": "Análisis IA completado con logs detallados",
            "analysis_result": analysis_result,
            "logs_info": "Revisa los logs del backend para ver la respuesta completa de OpenAI"
        }
        
    except Exception as e:
        logger.error(f"Error en análisis detallado: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(e)}")

@app.post("/test/ai-analysis-gpt5", tags=["Test"])
async def test_ai_analysis_gpt5(
    file_content: str = Body(..., description="Contenido del archivo .SCR para análisis con GPT-5"),
    file_name: str = Body("test_file.scr", description="Nombre del archivo"),
    db: Session = Depends(get_db)
):
    """Endpoint de prueba para análisis IA con GPT-5 (contexto ampliado)"""
    try:
        logger.info(f"=== ANÁLISIS IA CON GPT-5 ===")
        logger.info(f"Archivo: {file_name}")
        logger.info(f"Contenido: {len(file_content)} caracteres")
        
        # Crear configuración temporal para GPT-5
        from .domain.entities.configuration import LLMConfig, LLMProvider
        
        gpt5_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            api_key=llm_service.api_key,  # Usar la misma API key
            base_url=llm_service.base_url,
            model_name='gpt-5',  # Cambiar a GPT-5
            max_tokens=16384,  # Aumentar tokens para archivos completos
            temperature=0.3  # Reducir temperatura para análisis más preciso
        )
        
        # Crear servicio LLM temporal con GPT-5
        from .infrastructure.services.llm_service_impl import LLMServiceImpl
        gpt5_llm_service = LLMServiceImpl()
        await gpt5_llm_service.initialize(gpt5_config)
        
        # Crear servicios
        from .application.services.ai_analysis_service import AIAnalysisService
        from .application.services.nsdk_query_service import NSDKQueryService
        
        nsdk_query_service = NSDKQueryService(db)
        ai_service = AIAnalysisService(vectorization_use_case, gpt5_llm_service, nsdk_query_service)
        
        # Realizar análisis con GPT-5
        logger.info("Iniciando análisis IA con GPT-5...")
        analysis_result = await ai_service.analyze_scr_file(
            file_path=f"/test/{file_name}",
            file_content=file_content,
            file_name=file_name
        )
        
        logger.info("=== ANÁLISIS GPT-5 COMPLETADO ===")
        logger.info(f"Resultado: {analysis_result}")
        
        return {
            "status": "success",
            "message": "Análisis IA completado con GPT-5",
            "model_used": "gpt-5",
            "analysis_result": analysis_result,
            "logs_info": "Revisa los logs del backend para ver la respuesta completa de GPT-5"
        }
        
    except Exception as e:
        logger.error(f"Error en análisis GPT-5: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Error en análisis GPT-5: {str(e)}")

@app.post("/configurations/update-model-to-gpt5", tags=["Configuración"])
async def update_model_to_gpt5():
    """Actualizar la configuración activa para usar GPT-5"""
    try:
        # Obtener configuración activa
        active_config = await config_repo.find_active()
        if not active_config:
            raise HTTPException(status_code=404, detail="No hay configuración activa")
        
        # Actualizar el modelo a GPT-5
        if 'llmConfig' not in active_config.config_data:
            active_config.config_data['llmConfig'] = {}
        
        active_config.config_data['llmConfig']['modelName'] = 'gpt-5'
        active_config.config_data['llmConfig']['maxTokens'] = 16384
        active_config.config_data['llmConfig']['temperature'] = 0.3
        
        # Guardar cambios
        updated_config = await config_repo.update(active_config)
        
        # Reinicializar el servicio LLM
        await initialize_llm_service()
        
        logger.info("Modelo actualizado a GPT-5 exitosamente")
        return {
            "status": "success",
            "message": "Modelo actualizado a GPT-5 exitosamente",
            "config_id": str(updated_config.id),
            "model_name": "gpt-5",
            "max_tokens": 16384,
            "temperature": 0.3
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar modelo a GPT-5: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar modelo: {str(e)}")

@app.post("/configurations/update-model-to-gpt4", tags=["Configuración"])
async def update_model_to_gpt4():
    """Actualizar la configuración activa para usar GPT-4"""
    try:
        # Obtener configuración activa
        active_config = await config_repo.find_active()
        if not active_config:
            raise HTTPException(status_code=404, detail="No hay configuración activa")
        
        # Actualizar el modelo a GPT-4
        if 'llmConfig' not in active_config.config_data:
            active_config.config_data['llmConfig'] = {}
        
        active_config.config_data['llmConfig']['modelName'] = 'gpt-4'
        active_config.config_data['llmConfig']['maxTokens'] = 4096
        active_config.config_data['llmConfig']['temperature'] = 0.7
        
        # Guardar cambios
        updated_config = await config_repo.update(active_config)
        
        # Reinicializar el servicio LLM
        await initialize_llm_service()
        
        logger.info("Modelo actualizado a GPT-4 exitosamente")
        return {
            "status": "success",
            "message": "Modelo actualizado a GPT-4 exitosamente",
            "config_id": str(updated_config.id),
            "model_name": "gpt-4",
            "max_tokens": 4096,
            "temperature": 0.7
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al actualizar modelo a GPT-4: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar modelo: {str(e)}") 