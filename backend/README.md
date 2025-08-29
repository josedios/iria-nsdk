# 🏗️ Backend - IRIA NSDK Migration Platform

Backend desarrollado en **FastAPI** con **Arquitectura Hexagonal** para la plataforma de migración NSDK.

## 🏛️ Arquitectura

### **Arquitectura Hexagonal (Clean Architecture)**
```
┌─────────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                      │
├─────────────────────────────────────────────────────────────┤
│  Controllers │  Middleware │  Schemas │  DTOs             │
├─────────────────────────────────────────────────────────────┤
│                   APPLICATION LAYER                        │
├─────────────────────────────────────────────────────────────┤
│  Use Cases │  Services │  DTOs │  Validators             │
├─────────────────────────────────────────────────────────────┤
│                     DOMAIN LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  Entities │  Repositories │  Services │  Value Objects    │
├─────────────────────────────────────────────────────────────┤
│                 INFRASTRUCTURE LAYER                       │
├─────────────────────────────────────────────────────────────┤
│  Database │  Git │  LLM │  Vector Store │  External APIs │
└─────────────────────────────────────────────────────────────┘
```

### **Estructura de Directorios**
```
backend/
├── src/
│   ├── domain/                 # 🎯 Dominio - Reglas de Negocio
│   │   ├── entities/           # Entidades del dominio
│   │   ├── repositories/       # Puertos (Interfaces)
│   │   └── services/           # Servicios de dominio
│   ├── infrastructure/         # 🔌 Infraestructura - Adaptadores
│   │   ├── database/           # PostgreSQL adapter
│   │   ├── git/                # Git integration
│   │   ├── llm/                # LLM providers
│   │   └── vector_store/       # Vector stores
│   ├── application/            # 📋 Casos de uso
│   │   ├── use_cases/          # Lógica de aplicación
│   │   ├── services/           # Servicios de aplicación
│   │   └── dto/                # DTOs
│   └── presentation/           # 🌐 API REST
│       ├── controllers/        # Endpoints
│       ├── middleware/         # Middleware
│       └── schemas/            # Schemas Pydantic
├── migrations/                 # 🗄️ Esquemas de base de datos
├── tests/                      # 🧪 Tests
└── requirements.txt            # 📦 Dependencias
```

## 🚀 Instalación y Configuración

### **Prerrequisitos**
- Python 3.10+
- PostgreSQL 13+
- Git

### **Configuración Rápida**

1. **Crear entorno virtual**
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

2. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

3. **Configurar base de datos**
```bash
# Crear base de datos
createdb iria_nsdk

# Ejecutar esquema
psql -h localhost -U postgres -d iria_nsdk
\i migrations/01_complete_schema.sql
```

4. **Configurar variables de entorno**
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. **Ejecutar el servidor**
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 🗄️ Base de Datos

### **Esquemas Disponibles**
- **`migrations/01_complete_schema.sql`** - Esquema completo del sistema (compatible con PostgreSQL 13+)

### **Tablas del Sistema**
| Tabla | Descripción | Propósito |
|-------|-------------|-----------|
| `configurations` | Configuraciones del sistema | LLM, repositorios, vector stores |
| `nsdk_directories` | Estructura de directorios NSDK | Jerarquía de módulos y pantallas |
| `nsdk_file_analyses` | Análisis de archivos NSDK | Metadatos y análisis de código |
| `nsdk_sync_logs` | Logs de sincronización | Historial de operaciones |
| `nsdk_repository_metadata` | Metadatos de repositorios | Estado y estadísticas |
| `analyses` | Análisis generales del sistema | Compatibilidad legacy |

### **Consultas Útiles**
```sql
-- Verificar estado de repositorios
SELECT repository_name, sync_status, total_files, analyzed_files 
FROM nsdk_repository_metadata;

-- Contar archivos por tipo
SELECT file_type, COUNT(*) as total_files 
FROM nsdk_file_analyses 
GROUP BY file_type;

-- Estructura de directorios
SELECT name, path, level, file_count, dir_count 
FROM nsdk_directories 
WHERE repository_name = 'nsdk-sources' 
ORDER BY level, path;
```

## 🔌 API Endpoints

### **Configuración**
- `GET /configurations` - Listar configuraciones
- `POST /configurations` - Crear configuración
- `PUT /configurations/{id}` - Actualizar configuración
- `DELETE /configurations/{id}` - Eliminar configuración

### **Repositorios**
- `POST /repositories/clone` - Clonar repositorio
- `GET /repositories` - Listar repositorios
- `POST /repositories/vectorize` - Vectorizar repositorio

### **Módulos y Pantallas**
- `GET /modules` - Listar módulos
- `GET /screens` - Listar pantallas
- `GET /directories/root/{repository}` - Estructura raíz
- `GET /directories/{id}` - Contenido de directorio

### **Análisis**
- `POST /analysis/analyze` - Analizar pantalla con IA
- `GET /analysis/{id}` - Obtener análisis
- `GET /analysis` - Listar análisis

## 🧠 Servicios LLM

### **Proveedores Soportados**
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Ollama**: Modelos locales (Llama, Mistral)
- **Mistral**: Mistral 7B, Mixtral 8x7B

### **Funcionalidades**
- Análisis de código NSDK
- Generación de código Angular
- Generación de código Spring Boot
- Resúmenes y documentación
- Chat asistente

### **Configuración**
```python
# Ejemplo de configuración LLM
llm_config = {
    "provider": "openai",
    "api_key": "tu-api-key",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 4000
}
```

## 🔍 Vector Store

### **Proveedores Soportados**
- **FAISS**: Búsqueda local rápida
- **Qdrant**: Vector database distribuida
- **Chroma**: Vector store embebido

### **Funcionalidades**
- Indexación de código NSDK
- Búsqueda semántica
- Similitud de archivos
- Contexto para análisis IA

## 🧪 Testing

### **Ejecutar Tests**
```bash
# Tests unitarios
pytest tests/ -v

# Tests con cobertura
pytest tests/ -v --cov=src

# Tests específicos
pytest tests/test_llm_service.py -v
```

### **Estructura de Tests**
```
tests/
├── unit/                      # Tests unitarios
│   ├── test_domain/          # Tests de dominio
│   ├── test_application/     # Tests de aplicación
│   └── test_infrastructure/  # Tests de infraestructura
├── integration/               # Tests de integración
└── fixtures/                  # Datos de prueba
```

## 🐳 Docker

### **Construir Imagen**
```bash
docker build -t iria-backend .
```

### **Ejecutar Contenedor**
```bash
docker run -p 8000:8000 iria-backend
```

### **Docker Compose**
```bash
# Solo backend
docker-compose up backend

# Con base de datos
docker-compose up postgres backend
```

## 📊 Monitoreo y Logging

### **Logging**
- **Loguru** para logging estructurado
- **Niveles**: DEBUG, INFO, WARNING, ERROR
- **Formato**: JSON con timestamps y contexto

### **Métricas**
- Rendimiento de LLM
- Estadísticas de vectorización
- Progreso de migración
- Uso de recursos

### **Health Checks**
- `GET /health` - Estado del sistema
- `GET /health/db` - Estado de la base de datos
- `GET /health/llm` - Estado de los servicios LLM

## 🔧 Desarrollo

### **Comandos Útiles**
```bash
# Formatear código
black src/ tests/

# Linting
flake8 src/ tests/

# Type checking
mypy src/

# Pre-commit hooks
pre-commit install
```

### **Debugging**
```bash
# Debug con VS Code
# Usar la configuración "Debug Backend" en .vscode/launch.json

# Debug manual
python -m debugpy --listen 5678 --wait-for-client -m uvicorn src.main:app
```

## 🚨 Troubleshooting

### **Problemas Comunes**

#### **Error de Base de Datos**
```bash
# Verificar conexión
psql -h localhost -U postgres -d iria_nsdk

# Verificar esquema
\dt
```

#### **Error de LLM**
```bash
# Verificar configuración
curl http://localhost:8000/configurations

# Verificar logs
tail -f backend.log
```

#### **Error de Vector Store**
```bash
# Verificar estado
curl http://localhost:8000/health/vector-store

# Reiniciar servicio
docker-compose restart qdrant
```

## 📝 Historial de Cambios

- **v1.0.0** - Arquitectura hexagonal implementada
- **v1.0.1** - Servicios LLM integrados
- **v1.0.2** - Vector store implementado
- **v1.0.3** - Análisis de código NSDK

## 🆘 Soporte

- **Issues**: GitHub Issues
- **Documentación**: [README principal](../README.md)
- **API Docs**: http://localhost:8000/docs
- **Logs**: `backend.log`

---

*Backend desarrollado con FastAPI y Arquitectura Hexagonal*
