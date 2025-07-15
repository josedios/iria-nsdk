from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from .domain.entities.configuration import Configuration
from .application.dto.configuration_dto import ConfigurationDTO
from .infrastructure.repositories.configuration_repository_impl import ConfigurationRepositoryImpl
from .database import get_db
from sqlalchemy.orm import Session

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

# --- ENDPOINTS DE VECTOR STORE Y VECTORIZE ---
@app.post("/vectorize", tags=["Vectorización"])
def vectorize_repositories():
    """Iniciar vectorización de los repositorios"""
    return {"status": "started"}

@app.get("/vectorize/stats", tags=["Vectorización"])
def get_vectorization_stats():
    """Obtener estadísticas de vectorización"""
    return {}

@app.post("/vectorize/docs", tags=["Vectorización"])
def vectorize_documentation():
    """Vectorizar documentación técnica"""
    return {"status": "completed"}

@app.post("/vectorize/search", tags=["Vectorización"])
def search_similar_code():
    """Buscar código similar en el vector store"""
    return []

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