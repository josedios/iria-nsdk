# 🚀 Guía de Inicio Rápido - Prompt Maestro

Esta guía te ayudará a tener **Prompt Maestro** funcionando en menos de 10 minutos.

## 📋 Prerrequisitos

Asegúrate de tener instalado:
- [Docker](https://www.docker.com/get-started) y Docker Compose
- [Git](https://git-scm.com/downloads)
- [Node.js 18+](https://nodejs.org/) (opcional, para desarrollo)
- [Python 3.10+](https://www.python.org/downloads/) (opcional, para desarrollo)

## 🎯 Opción 1: Inicio Rápido con Docker

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/prompt-maestro.git
cd prompt-maestro
```

### 2. Configurar variables de entorno
```bash
cp backend/.env.example backend/.env
# Editar backend/.env con tus configuraciones (al menos OPENAI_API_KEY)
```

### 3. Ejecutar con Docker Compose
```bash
# Iniciar todos los servicios
docker-compose up -d

# Ver los logs
docker-compose logs -f
```

### 4. Acceder a la aplicación
- **Frontend**: http://localhost:4200
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Database**: postgres://postgres:postgres@localhost:5432/prompt_maestro

¡Listo! 🎉 Ya tienes Prompt Maestro funcionando.

## 🛠 Opción 2: Desarrollo Local

### Backend

```bash
cd backend

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Iniciar base de datos (con Docker)
docker run -d \
  --name prompt-maestro-db \
  -e POSTGRES_DB=prompt_maestro \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 \
  postgres:15-alpine

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn src.main:app --reload
```

### Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Iniciar servidor de desarrollo
npm start
```

## 🔧 Configuración Básica

### 1. Configurar OpenAI
En `backend/.env`:
```bash
OPENAI_API_KEY=sk-tu-api-key-aqui
OPENAI_MODEL=gpt-4
```

### 2. Configurar Repositorios
Desde la UI en http://localhost:4200/config:
- **Repositorio Origen**: URL del repo NSDK
- **Repositorio Destino**: URL del repo Angular/Spring Boot
- **Credenciales**: Token de acceso o SSH key

### 3. Configurar Vector Store
- **FAISS**: Funciona sin configuración adicional
- **Qdrant**: Incluido en docker-compose
- **Chroma**: Configuración automática

## 📊 Primeros Pasos

### 1. Configurar Proyecto
1. Ve a **Configuración** (`/config`)
2. Configura tus repositorios
3. Selecciona tu proveedor LLM
4. Guarda la configuración

### 2. Vectorizar Código
1. Ve a **Conocimiento** (`/knowledge`)
2. Haz clic en "Vectorizar Repositorios"
3. Espera a que termine el proceso

### 3. Explorar Módulos
1. Ve a **Módulos** (`/modules`)
2. Explora el árbol de módulos
3. Selecciona una pantalla para analizar

### 4. Analizar Pantalla
1. Haz clic en "Analizar" en una pantalla
2. Revisa los resultados en el modal
3. Ve las 3 pestañas: Frontend, Backend, API

### 5. Generar Código
1. En una pantalla analizada, haz clic en "Generar Código"
2. Se creará una rama automáticamente
3. Revisa el código generado en tu repo

## 🔍 Verificar Instalación

### Healthcheck
```bash
curl http://localhost:8000/health
```

### Verificar Servicios
```bash
# Backend
curl http://localhost:8000/api/health

# Frontend
curl http://localhost:4200

# Base de datos
docker exec -it prompt-maestro-db psql -U postgres -d prompt_maestro -c "SELECT 1;"
```

## 🐛 Solución de Problemas

### Backend no inicia
```bash
# Verificar logs
docker-compose logs backend

# Verificar base de datos
docker-compose ps postgres

# Reiniciar servicios
docker-compose restart backend
```

### Frontend no carga
```bash
# Verificar logs
docker-compose logs frontend

# Verificar dependencias
docker-compose exec frontend npm list

# Reconstruir
docker-compose build frontend
```

### Error de conexión a base de datos
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps postgres

# Verificar variables de entorno
docker-compose exec backend env | grep DATABASE
```

## 📞 Soporte

Si tienes problemas:

1. **Revisa los logs**: `docker-compose logs -f`
2. **Verifica la configuración**: Archivo `.env` y variables
3. **Consulta la documentación**: [docs/](docs/)
4. **Abre un issue**: [GitHub Issues](https://github.com/tu-usuario/prompt-maestro/issues)

## 🎯 Próximos Pasos

Una vez que tengas el sistema funcionando:

1. **Lee la documentación completa** en `README.md`
2. **Explora las características avanzadas**
3. **Configura tu pipeline de CI/CD**
4. **Personaliza las plantillas de código**
5. **Integra con tu flujo de trabajo**

---

¡Disfruta usando **Prompt Maestro** para modernizar tus aplicaciones NSDK! 🚀