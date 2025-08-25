from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any, Optional
from .domain.entities.configuration import Configuration
from .application.dto.configuration_dto import ConfigurationDTO
from .infrastructure.repositories.configuration_repository_impl import ConfigurationRepositoryImpl
from .database import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel
from .application.use_cases.test_connections_use_case import TestConnectionsUseCase

app = FastAPI(title="Prompt Maestro Backend API")

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

class TestConnectionsRequest(BaseModel):
    config_data: Dict[str, Any]

class TestConnectionsResult(BaseModel):
    service: str
    status: str  # "success" o "error"
    message: str

@app.get("/configurations", response_model=List[ConfigurationDTO], tags=["Configuración"])
def get_configurations():
    """Listar todas las configuraciones"""
    configs = config_repo.db.query(Configuration).all()
    return configs

@app.get("/configurations/active", tags=["Configuración"])
def get_active_configuration():
    """Obtener la configuración activa"""
    return {}

@app.get("/configurations/{config_id}", response_model=ConfigurationDTO, tags=["Configuración"])
def get_configuration(config_id: str):
    """Obtener una configuración por ID"""
    config = config_repo.db.query(Configuration).filter(Configuration.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    return config

@app.post("/configurations", response_model=ConfigurationDTO, tags=["Configuración"])
def create_configuration(config: ConfigurationDTO):
    """Crear una nueva configuración"""
    db_config = Configuration(
        name=config.name,
        description=config.description,
        config_data=config.config_data
    )
    config_repo.db.add(db_config)
    config_repo.db.commit()
    config_repo.db.refresh(db_config)
    return db_config

@app.put("/configurations/{config_id}", response_model=ConfigurationDTO, tags=["Configuración"])
def update_configuration(config_id: str, config: ConfigurationDTO):
    """Actualizar una configuración"""
    db_config = config_repo.db.query(Configuration).filter(Configuration.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    db_config.name = config.name
    db_config.description = config.description
    db_config.config_data = config.config_data
    config_repo.db.commit()
    config_repo.db.refresh(db_config)
    return db_config

@app.delete("/configurations/{config_id}", tags=["Configuración"])
def delete_configuration(config_id: str):
    """Eliminar una configuración"""
    db_config = config_repo.db.query(Configuration).filter(Configuration.id == config_id).first()
    if not db_config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    config_repo.db.delete(db_config)
    config_repo.db.commit()
    return {"deleted": True}

@app.post("/configurations/{config_id}/activate", tags=["Configuración"])
def activate_configuration(config_id: str):
    """Activar una configuración"""
    return {"activated": True}

@app.post("/configurations/test-connections", response_model=List[TestConnectionsResult], tags=["Configuración"])
def test_connections(request: TestConnectionsRequest):
    use_case = TestConnectionsUseCase()
    return use_case.execute(request.config_data)

# --- ENDPOINTS DE VECTOR STORE Y VECTORIZE ---
from .application.use_cases.vectorization_use_case import VectorizationUseCase
from .infrastructure.services.nsdk_vectorization_service import NSDKVectorizationService
from .infrastructure.services.vector_store_service_impl import VectorStoreServiceImpl
from .infrastructure.services.llm_service_impl import LLMServiceImpl

# Instanciar servicios
vector_store_service = VectorStoreServiceImpl()
llm_service = LLMServiceImpl()
nsdk_vectorization_service = NSDKVectorizationService(vector_store_service, llm_service)
vectorization_use_case = VectorizationUseCase(nsdk_vectorization_service)

class VectorizeRepositoryRequest(BaseModel):
    repo_url: str
    branch: str = 'main'
    username: Optional[str] = None
    token: Optional[str] = None

class VectorizeModuleRequest(BaseModel):
    module_path: str
    repo_url: str
    branch: str = 'main'

class SearchCodeRequest(BaseModel):
    query: str
    limit: int = 10

@app.post("/vectorize/repository", tags=["Vectorización"])
async def vectorize_repository(request: VectorizeRepositoryRequest):
    """Vectorizar un repositorio completo de NSDK"""
    try:
        batch = await vectorization_use_case.vectorize_repository(
            repo_url=request.repo_url,
            branch=request.branch,
            username=request.username,
            token=request.token
        )
        return {
            "status": "started",
            "batch_id": batch.id,
            "batch_name": batch.name,
            "total_files": batch.total_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en vectorización: {str(e)}")

@app.post("/vectorize/module", tags=["Vectorización"])
async def vectorize_module(request: VectorizeModuleRequest):
    """Vectorizar un módulo específico"""
    try:
        batch = await vectorization_use_case.vectorize_module(
            module_path=request.module_path,
            repo_url=request.repo_url,
            branch=request.branch
        )
        return {
            "status": "started",
            "batch_id": batch.id,
            "batch_name": batch.name,
            "total_files": batch.total_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en vectorización del módulo: {str(e)}")

@app.get("/vectorize/stats", tags=["Vectorización"])
def get_vectorization_stats():
    """Obtener estadísticas de vectorización"""
    try:
        stats = vectorization_use_case.get_vectorization_stats()
        return stats
    except Exception as e:
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
    """Listar todos los módulos"""
    return []

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
    """Listar todas las pantallas"""
    return []

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