from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from dotenv import load_dotenv

# Importar la base desde el archivo separado
from .database_base import Base

# Cargar variables de entorno desde .env
load_dotenv()

# Configuración de la base de datos
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./nsdk_migration.db")

# Crear engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
else:
    engine = create_engine(DATABASE_URL)

# Crear sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Función para obtener la sesión de BD
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Crear todas las tablas
def create_tables():
    # Importar todas las entidades para que SQLAlchemy las registre
    from .domain.entities.configuration import Configuration
    from .domain.entities.ai_analysis_result import AIAnalysisResult
    from .domain.entities.nsdk_file_analysis import NSDKFileAnalysis
    from .domain.entities.vectorization_batch import VectorizationBatch
    from .domain.entities.nsdk_directory import NSDKDirectory
    from .domain.entities.vector_embedding import VectorEmbedding
    
    Base.metadata.create_all(bind=engine) 