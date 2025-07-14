# 🚀 Prompt Maestro - Plataforma de Migración NSDK

Una plataforma completa para migrar aplicaciones legacy desarrolladas en NSDK hacia una arquitectura moderna con **Angular** (frontend) y **Spring Boot** (backend), asistida con IA.

## 🎯 Características Principales

- **Arquitectura Hexagonal** en el backend con FastAPI
- **Frontend Moderno** con Angular 17+ y Angular Material
- **Soporte Multi-LLM** (OpenAI, Ollama, Mistral)
- **Vector Store** para búsqueda semántica (FAISS, Qdrant, Chroma)
- **Integración Git** completa con creación automática de ramas
- **Análisis Inteligente** de código NSDK con IA
- **Generación de Código** Angular y Spring Boot

## 🏗 Arquitectura del Sistema

### Backend (FastAPI + Arquitectura Hexagonal)
```
backend/
├── src/
│   ├── domain/                 # Dominio - Reglas de Negocio
│   │   ├── entities/           # Entidades del dominio
│   │   ├── repositories/       # Puertos (Interfaces)
│   │   └── services/           # Servicios de dominio
│   ├── infrastructure/         # Infraestructura - Adaptadores
│   │   ├── database/           # PostgreSQL
│   │   ├── git/                # Git integration
│   │   ├── llm/                # LLM providers
│   │   └── vector_store/       # Vector stores
│   ├── application/            # Casos de uso
│   │   ├── use_cases/          # Lógica de aplicación
│   │   └── dto/                # DTOs
│   └── presentation/           # API REST
│       ├── controllers/        # Endpoints
│       ├── middleware/         # Middleware
│       └── schemas/            # Schemas Pydantic
└── tests/                      # Tests
```

### Frontend (Angular 17+ + Angular Material)
```
frontend/
├── src/
│   ├── app/
│   │   ├── core/              # Servicios centrales
│   │   ├── shared/            # Componentes compartidos
│   │   ├── features/          # Módulos funcionales
│   │   │   ├── dashboard/     # Dashboard con métricas
│   │   │   ├── modules/       # Explorador de módulos
│   │   │   ├── config/        # Configuración
│   │   │   └── knowledge/     # Gestión de conocimiento
│   │   └── layout/            # Layout principal
│   ├── assets/                # Recursos estáticos
│   └── environments/          # Configuraciones
```

## 🔧 Instalación y Configuración

### Prerrequisitos
- Python 3.10+
- Node.js 18+
- PostgreSQL 13+
- Git

### Backend Setup

1. **Crear entorno virtual**
```bash
cd backend
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
# Crear base de datos PostgreSQL
createdb prompt_maestro

# Ejecutar migraciones
alembic upgrade head
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

### Frontend Setup

1. **Instalar dependencias**
```bash
cd frontend
npm install
```

2. **Ejecutar el servidor de desarrollo**
```bash
npm start
```

3. **Acceder a la aplicación**
```
http://localhost:4200
```

## 📊 Flujos Principales

### 1. Configuración Inicial
- Configurar repositorio origen (NSDK)
- Configurar repositorio destino (Angular/Spring Boot)
- Configurar proveedor LLM (OpenAI/Ollama/Mistral)
- Configurar Vector Store

### 2. Vectorización
- Clonar repositorios
- Vectorizar código NSDK (.SCR, .NCL)
- Indexar documentación técnica
- Crear índice de módulos y pantallas

### 3. Análisis con IA
- Seleccionar pantalla desde el explorador
- Análisis automático con contexto vectorizado
- Resultados en 3 categorías:
  - **Frontend**: Campos, validaciones, UI
  - **Backend**: Lógica de negocio, SQL, APIs
  - **API**: Endpoints, OpenAPI, modelos

### 4. Generación de Código
- Crear rama automática: `migracion/<modulo>/<pantalla>`
- Generar código Angular (componentes, servicios)
- Generar código Spring Boot (controladores, servicios)
- Generar especificación OpenAPI
- Commit y push automáticos

## 🎨 Interfaz de Usuario

### Dashboard
- Métricas de progreso de migración
- Estadísticas de módulos y pantallas
- Actividad reciente
- Acciones rápidas
- Estado del sistema

### Explorador de Módulos
- Árbol jerárquico de módulos y pantallas
- Estados de migración visuales
- Acciones por pantalla (analizar, generar, asignar)
- Modal de análisis detallado con 3 pestañas

### Configuración
- Gestión de repositorios
- Configuración de LLM
- Configuración de Vector Store
- Validación de conexiones

## 🔌 Integraciones

### Proveedores LLM
- **OpenAI**: GPT-4, GPT-3.5-turbo
- **Ollama**: Modelos locales (Llama, Mistral, etc.)
- **Mistral**: Mistral 7B, Mixtral 8x7B

### Vector Stores
- **FAISS**: Búsqueda local rápida
- **Qdrant**: Vector database distribuida
- **Chroma**: Vector store embebido

### Sistemas de Control de Versiones
- **Git**: GitHub, GitLab, BitBucket
- **Autenticación**: Token, SSH key
- **Operaciones**: Clone, branch, commit, push

## 🚀 Despliegue

### Docker
```bash
# Construir y ejecutar con Docker Compose
docker-compose up --build

# Solo backend
docker-compose up backend

# Solo frontend
docker-compose up frontend
```

### Producción
```bash
# Backend
gunicorn src.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend
ng build --configuration production
```

## 📈 Monitoreo y Logging

- **Logging estructurado** con Loguru
- **Métricas de rendimiento** de LLM
- **Estadísticas de vectorización**
- **Progreso de migración** en tiempo real

## 🧪 Testing

### Backend
```bash
pytest tests/ -v --cov=src
```

### Frontend
```bash
npm test
ng e2e
```

## 📚 Documentación

- **API Documentation**: http://localhost:8000/docs
- **Frontend Storybook**: http://localhost:6006
- **Architecture Guide**: docs/architecture/
- **API Reference**: docs/api/

## 🤝 Contribución

1. Fork el proyecto
2. Crear rama feature (`git checkout -b feature/amazing-feature`)
3. Commit cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abrir Pull Request

## 📄 Licencia

Este proyecto está licenciado bajo la MIT License - ver [LICENSE](LICENSE) para detalles.

## 🆘 Soporte

- **Issues**: GitHub Issues
- **Email**: support@prompt-maestro.com
- **Documentation**: https://docs.prompt-maestro.com

---

## 🎯 Roadmap

### v1.0 (Actual)
- ✅ Arquitectura hexagonal backend
- ✅ Frontend Angular con Material
- ✅ Integración LLM básica
- ✅ Vector store para búsqueda
- ✅ Análisis de pantallas NSDK
- ✅ Generación de código básica

### v1.1 (Próximo)
- 🔄 Análisis batch de múltiples pantallas
- 🔄 Integración con IDE (VS Code extension)
- 🔄 Plantillas de código personalizables
- 🔄 Métricas avanzadas de migración

### v1.2 (Futuro)
- 📋 Soporte para más lenguajes destino
- 📋 Integración con CI/CD
- 📋 Dashboard de gestión de equipos
- 📋 API pública para integraciones

## 🎉 Reconocimientos

- **FastAPI** por el excelente framework
- **Angular Material** por los componentes UI
- **OpenAI** por la API de IA
- **Qdrant** por el vector store

---

*Construido con ❤️ para modernizar aplicaciones legacy*