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
        
        db.close()
        return {
            "message": "Conexión a base de datos exitosa",
            "status": "success",
            "configs_count": len(configs),
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
def get_active_configuration():
    """Obtener la configuración activa"""
    return {}

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
unified_vectorization_service = UnifiedVectorizationService(vector_store_service, llm_service, repo_manager)
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