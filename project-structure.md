# 🚀 Prompt Maestro - Estructura del Proyecto

## 📁 Estructura General

```
prompt-maestro/
├── backend/                     # FastAPI Backend con Arquitectura Hexagonal
│   ├── src/
│   │   ├── domain/             # Dominio - Entidades y Reglas de Negocio
│   │   │   ├── entities/
│   │   │   ├── repositories/   # Puertos (Interfaces)
│   │   │   └── services/       # Servicios de dominio
│   │   ├── infrastructure/     # Infraestructura - Adaptadores
│   │   │   ├── database/
│   │   │   ├── git/
│   │   │   ├── llm/
│   │   │   └── vector_store/
│   │   ├── application/        # Casos de uso
│   │   │   ├── use_cases/
│   │   │   └── dto/
│   │   └── presentation/       # API REST
│   │       ├── controllers/
│   │       ├── middleware/
│   │       └── schemas/
│   ├── tests/
│   ├── requirements.txt
│   ├── docker-compose.yml
│   └── Dockerfile
├── frontend/                   # Angular Frontend
│   ├── src/
│   │   ├── app/
│   │   │   ├── core/          # Servicios centrales
│   │   │   ├── shared/        # Componentes compartidos
│   │   │   ├── features/      # Módulos de funcionalidades
│   │   │   │   ├── dashboard/
│   │   │   │   ├── modules/
│   │   │   │   ├── config/
│   │   │   │   └── knowledge/
│   │   │   └── layout/        # Layout principal
│   │   ├── assets/
│   │   └── environments/
│   ├── angular.json
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml          # Orquestación completa
├── README.md
└── docs/                       # Documentación técnica
    ├── api/
    ├── architecture/
    └── deployment/
```

## 🏗 Arquitectura Hexagonal (Backend)

### Dominio (Core)
- **Entities**: Módulos, Pantallas, Configuración, Análisis
- **Repositories**: Interfaces para persistencia
- **Services**: Lógica de negocio pura

### Infraestructura (Adaptadores)
- **Database**: PostgreSQL adapter
- **Git**: GitLab/GitHub integration
- **LLM**: OpenAI, Ollama, Mistral adapters
- **Vector Store**: FAISS, Qdrant, Chroma adapters

### Aplicación (Use Cases)
- **ConfigurationUseCase**: Gestión de configuración
- **VectorizationUseCase**: Indexación y vectorización
- **AnalysisUseCase**: Análisis con IA
- **GenerationUseCase**: Generación de código

### Presentación (API)
- **Controllers**: REST endpoints
- **Schemas**: Pydantic models
- **Middleware**: Auth, CORS, logging

## 🎨 Estructura Angular (Frontend)

### Core
- **Services**: HTTP clients, auth, state management
- **Guards**: Route protection
- **Interceptors**: HTTP interceptors

### Shared
- **Components**: Reutilizables
- **Directives**: Custom directives
- **Pipes**: Data transformation

### Features
- **Dashboard**: Resumen y métricas
- **Modules**: Explorador de módulos
- **Config**: Configuración de repos y LLM
- **Knowledge**: Gestión de documentación

### Layout
- **Navigation**: Menú lateral
- **Header**: Top bar
- **Footer**: Bottom info