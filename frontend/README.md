# 🎨 Frontend - IRIA NSDK Migration Platform

Frontend desarrollado en **Angular 17+** con **Angular Material** para la plataforma de migración NSDK.

## 🏗️ Arquitectura

### **Arquitectura Angular (Feature-Based)**
```
┌─────────────────────────────────────────────────────────────┐
│                        CORE LAYER                          │
├─────────────────────────────────────────────────────────────┤
│  Services │  Guards │  Interceptors │  Models             │
├─────────────────────────────────────────────────────────────┤
│                     SHARED LAYER                            │
├─────────────────────────────────────────────────────────────┤
│  Components │  Directives │  Pipes │  Utilities           │
├─────────────────────────────────────────────────────────────┤
│                    FEATURES LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  Dashboard │  Modules │  Config │  Knowledge             │
├─────────────────────────────────────────────────────────────┤
│                      LAYOUT LAYER                           │
├─────────────────────────────────────────────────────────────┤
│  Navigation │  Header │  Footer │  Sidebar               │
└─────────────────────────────────────────────────────────────┘
```

### **Estructura de Directorios**
```
frontend/
├── src/
│   ├── app/
│   │   ├── core/              # 🎯 Servicios centrales
│   │   │   ├── services/      # HTTP, auth, state
│   │   │   ├── guards/        # Route protection
│   │   │   ├── interceptors/  # HTTP interceptors
│   │   │   └── models/        # Interfaces y tipos
│   │   ├── shared/            # 🔄 Componentes compartidos
│   │   │   ├── components/    # UI components
│   │   │   ├── directives/    # Custom directives
│   │   │   ├── pipes/         # Data transformation
│   │   │   └── utils/         # Utilities
│   │   ├── features/          # 📋 Módulos funcionales
│   │   │   ├── dashboard/     # Dashboard principal
│   │   │   ├── modules/       # Explorador de módulos
│   │   │   ├── config/        # Configuración
│   │   │   └── knowledge/     # Gestión de conocimiento
│   │   └── layout/            # 🎨 Layout principal
│   │       ├── navigation/    # Menú lateral
│   │       ├── header/        # Barra superior
│   │       └── footer/        # Pie de página
│   ├── assets/                # 📁 Recursos estáticos
│   ├── environments/          # ⚙️ Configuraciones
│   └── styles/                # 🎨 Estilos globales
├── angular.json               # Configuración Angular
├── package.json               # Dependencias
└── tsconfig.json              # Configuración TypeScript
```

## 🚀 Instalación y Configuración

### **Prerrequisitos**
- Node.js 18+
- npm 9+ o yarn 1.22+
- Angular CLI 17+

### **Configuración Rápida**

1. **Instalar Angular CLI**
```bash
npm install -g @angular/cli@17
```

2. **Instalar dependencias**
```bash
npm install
```

3. **Configurar variables de entorno**
```bash
# Editar src/environments/environment.ts
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000'
};
```

4. **Ejecutar servidor de desarrollo**
```bash
npm start
# o
ng serve --host 0.0.0.0 --port 4200
```

5. **Acceder a la aplicación**
```
http://localhost:4200
```

## 🎨 Componentes Principales

### **Dashboard**
- **Métricas de migración** - Progreso general del proyecto
- **Estadísticas de módulos** - Conteo y estado
- **Actividad reciente** - Últimas operaciones
- **Acciones rápidas** - Botones de acceso directo

### **Explorador de Módulos**
- **Árbol jerárquico** - Estructura de directorios NSDK
- **Estados visuales** - Indicadores de progreso
- **Acciones por pantalla** - Analizar, generar, asignar
- **Modal de análisis** - 3 pestañas: Frontend, Backend, API

### **Configuración**
- **Gestión de repositorios** - Origen y destino
- **Configuración LLM** - Proveedores y modelos
- **Vector Store** - Configuración de búsqueda
- **Validación de conexiones** - Health checks

### **Gestión de Conocimiento**
- **Documentación técnica** - Manuales y guías
- **Plantillas de código** - Estructuras reutilizables
- **Historial de análisis** - Resultados previos
- **Exportación de datos** - Reportes y métricas

## 🔌 Integración con Backend

### **Servicios HTTP**
```typescript
// Ejemplo de servicio
@Injectable({
  providedIn: 'root'
})
export class ModuleService {
  constructor(private http: HttpClient) {}

  getModules(): Observable<Module[]> {
    return this.http.get<Module[]>(`${environment.apiUrl}/modules`);
  }

  analyzeModule(moduleId: string): Observable<Analysis> {
    return this.http.post<Analysis>(`${environment.apiUrl}/analysis/analyze`, {
      moduleId
    });
  }
}
```

### **Interceptores**
- **Auth Interceptor** - Tokens de autenticación
- **Error Interceptor** - Manejo de errores HTTP
- **Loading Interceptor** - Indicadores de carga
- **Logging Interceptor** - Log de requests/responses

### **Estado de la Aplicación**
- **NgRx Store** - Estado global (opcional)
- **Services con BehaviorSubject** - Estado local
- **Local Storage** - Persistencia de configuraciones
- **Session Storage** - Datos temporales

## 🎨 UI/UX

### **Angular Material**
- **Componentes base** - Botones, inputs, cards
- **Layout components** - Grid, flexbox, sidenav
- **Data components** - Tables, pagination, sorting
- **Navigation** - Menús, breadcrumbs, tabs

### **Tema Personalizado**
```scss
// Variables de tema
$primary-palette: mat-palette($mat-blue);
$accent-palette: mat-palette($mat-orange);
$warn-palette: mat-palette($mat-red);

// Tema personalizado
$custom-theme: mat-light-theme(
  $primary-palette,
  $accent-palette,
  $warn-palette
);
```

### **Responsive Design**
- **Mobile First** - Diseño adaptativo
- **Breakpoints** - xs, sm, md, lg, xl
- **Flexbox Layout** - Componentes flexibles
- **CSS Grid** - Layouts complejos

## 🧪 Testing

### **Ejecutar Tests**
```bash
# Tests unitarios
npm test

# Tests con cobertura
npm run test:coverage

# Tests E2E
npm run e2e

# Tests específicos
ng test --include="**/modules/**/*.spec.ts"
```

### **Estructura de Tests**
```
src/
├── app/
│   └── features/
│       └── modules/
│           ├── modules.component.ts
│           ├── modules.component.spec.ts
│           └── modules.component.e2e-spec.ts
└── test/
    ├── unit/                   # Tests unitarios
    ├── integration/            # Tests de integración
    └── e2e/                    # Tests end-to-end
```

### **Testing Utilities**
- **Jasmine** - Framework de testing
- **Karma** - Test runner
- **Protractor** - E2E testing
- **Testing Library** - Helpers para testing

## 🐳 Docker

### **Construir Imagen**
```bash
docker build -t iria-frontend .
```

### **Ejecutar Contenedor**
```bash
docker run -p 4200:4200 iria-frontend
```

### **Docker Compose**
```bash
# Solo frontend
docker-compose up frontend

# Con backend
docker-compose up frontend backend
```

## 📊 Monitoreo y Performance

### **Performance**
- **Lazy Loading** - Carga bajo demanda
- **Tree Shaking** - Eliminación de código no usado
- **Bundle Analysis** - Análisis de tamaño
- **Service Workers** - Caching offline

### **Monitoreo**
- **Angular DevTools** - Debugging en tiempo real
- **Performance Profiler** - Métricas de rendimiento
- **Error Tracking** - Captura de errores
- **Analytics** - Métricas de usuario

### **Optimizaciones**
```typescript
// Lazy loading de módulos
const routes: Routes = [
  {
    path: 'modules',
    loadChildren: () => import('./features/modules/modules.module')
      .then(m => m.ModulesModule)
  }
];

// OnPush change detection
@Component({
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class ModuleComponent {
  // Componente optimizado
}
```

## 🔧 Desarrollo

### **Comandos Útiles**
```bash
# Generar componente
ng generate component features/modules/module-detail

# Generar servicio
ng generate service core/services/module

# Generar pipe
ng generate pipe shared/pipes/module-filter

# Generar directive
ng generate directive shared/directives/highlight
```

### **Debugging**
```bash
# Debug con VS Code
# Usar la configuración "Debug Frontend" en .vscode/launch.json

# Debug manual
ng serve --configuration development
```

### **Code Quality**
```bash
# Linting
npm run lint

# Formatear código
npm run format

# Type checking
npm run type-check

# Pre-commit hooks
npm run pre-commit
```

## 🚨 Troubleshooting

### **Problemas Comunes**

#### **Error de Compilación**
```bash
# Limpiar cache
npm run clean

# Reinstalar dependencias
rm -rf node_modules package-lock.json
npm install
```

#### **Error de CORS**
```bash
# Verificar configuración del backend
# Asegurar que CORS esté habilitado

# Configurar proxy en angular.json
{
  "proxyConfig": "src/proxy.conf.json"
}
```

#### **Error de Build**
```bash
# Verificar versión de Node.js
node --version  # Debe ser 18+

# Verificar versión de Angular CLI
ng version

# Limpiar build
ng build --configuration production
```

## 📝 Historial de Cambios

- **v1.0.0** - Angular 17 implementado
- **v1.0.1** - Angular Material integrado
- **v1.0.2** - Componentes principales creados
- **v1.0.3** - Integración con backend

## 🆘 Soporte

- **Issues**: GitHub Issues
- **Documentación**: [README principal](../README.md)
- **Angular Docs**: https://angular.io/docs
- **Material Docs**: https://material.angular.io/

---

*Frontend desarrollado con Angular 17+ y Angular Material*
