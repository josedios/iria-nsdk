# 🚀 Guía de Desarrollo - IRIA NSDK

## Configuración Rápida

### 1. Ejecutar el script de configuración
```powershell
.\setup-dev.ps1
```

### 2. Configurar Base de Datos PostgreSQL
Tienes varias opciones:

#### Opción A: Docker (Recomendado)
```powershell
docker run --name iria-postgres -e POSTGRES_DB=iria_nsdk -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres:15-alpine
```

#### Opción B: Instalación nativa
1. Descarga PostgreSQL desde: https://www.postgresql.org/download/windows/
2. Instala con usuario: `postgres`, contraseña: `postgres`
3. Crea la base de datos: `iria_nsdk`

## 🐛 Debugging en Cursor/VS Code

### Configuraciones Disponibles

1. **Debug Backend (FastAPI)**
   - Debuggea solo el servidor backend
   - Incluye hot reload automático

2. **Debug Frontend (Angular)**
   - Debuggea solo el frontend
   - Abre Chrome con debugging habilitado

3. **Debug Full Stack** ⭐ (Recomendado)
   - Debuggea frontend y backend simultáneamente
   - Inicia ambos servidores automáticamente

### Cómo usar

1. Presiona `Ctrl+Shift+P`
2. Selecciona "Debug: Start Debugging"
3. Elige la configuración deseada
4. ¡Listo! Los breakpoints funcionarán en ambos lados

## 🛠️ Comandos Manuales

### Backend
```powershell
cd backend
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1
# Iniciar servidor
uvicorn src.main:app --reload --port 8000
```

### Frontend
```powershell
cd frontend
npm start
```

## 📁 Estructura del Proyecto

```
iria-nsdk/
├── backend/                 # FastAPI backend
│   ├── src/
│   │   ├── main.py         # Punto de entrada
│   │   ├── application/    # Casos de uso
│   │   └── domain/         # Entidades y repositorios
│   └── requirements.txt
├── frontend/               # Angular frontend
│   ├── src/
│   │   ├── app/
│   │   └── main.ts
│   └── package.json
└── .vscode/               # Configuraciones de debugging
    ├── launch.json
    ├── tasks.json
    └── settings.json
```

## 🔧 Variables de Entorno

### Backend
```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/iria_nsdk
ENVIRONMENT=development
PYTHONPATH=./backend
```

### Frontend
```env
API_URL=http://localhost:8000
NODE_ENV=development
```

## 🐛 Troubleshooting

### Error: "Python interpreter not found"
1. Asegúrate de que Python esté instalado
2. Ejecuta `.\setup-dev.ps1` para crear el entorno virtual
3. En Cursor, presiona `Ctrl+Shift+P` → "Python: Select Interpreter"
4. Selecciona `./backend/.venv/Scripts/python.exe`

### Error: "npm not found"
1. Instala Node.js desde: https://nodejs.org/
2. Reinicia Cursor después de la instalación

### Error: "Database connection failed"
1. Verifica que PostgreSQL esté ejecutándose en el puerto 5432
2. Confirma las credenciales: usuario `postgres`, contraseña `postgres`
3. Asegúrate de que la base de datos `iria_nsdk` exista

## 🎯 Próximos Pasos

1. ✅ Configurar entorno de desarrollo
2. ✅ Configurar base de datos
3. 🔄 Implementar funcionalidades específicas
4. 🧪 Escribir tests
5. 🚀 Desplegar

¡Happy coding! 🎉 