import { FlatTreeControl } from '@angular/cdk/tree';
import { CommonModule } from '@angular/common';
import { HttpClientModule } from '@angular/common/http';
import { Component, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatTreeFlatDataSource, MatTreeFlattener, MatTreeModule } from '@angular/material/tree';
import { ModulesService, NSDKModule, NSDKScreen, RepositoryTreeNode, NSDKAnalysis, AnalysisStatus } from './modules.service';

interface ModuleNode {
  name: string;
  type: 'module' | 'screen' | 'include' | 'program' | 'config' | 'document' | 'other' | 'directory';
  status?: 'pending' | 'analyzing' | 'analyzed' | 'generated' | 'error';
  path: string;
  children?: ModuleNode[];
  id?: string;
  developer?: string;
  complexity?: number;
  estimatedHours?: number;
  is_file?: boolean;
  is_dir?: boolean;
  file_count?: number;
  dir_count?: number;
  size_kb?: number;
  extension?: string;
  line_count?: number;
  char_count?: number;
  function_count?: number;
  functions?: string[];
  field_count?: number;
  fields?: string[];
  button_count?: number;
  buttons?: string[];
  isLoading?: boolean; // Nuevo campo para indicar si se está cargando el contenido
}

interface FlatNode {
  expandable: boolean;
  name: string;
  type: 'module' | 'screen' | 'include' | 'program' | 'config' | 'document' | 'other' | 'directory';
  status?: 'pending' | 'analyzing' | 'analyzed' | 'generated' | 'error';
  level: number;
  path: string;
  id?: string;
  developer?: string;
  complexity?: number;
  estimatedHours?: number;
  is_file?: boolean;
  is_dir?: boolean;
  file_count?: number;
  dir_count?: number;
  size_kb?: number;
  extension?: string;
  line_count?: number;
  char_count?: number;
  function_count?: number;
  functions?: string[];
  field_count?: number;
  fields?: string[];
  button_count?: number;
  buttons?: string[];
  isLoading?: boolean; // Nuevo campo para indicar si se está cargando el contenido
}

interface AnalysisData {
  frontend: {
    fields: any[];
    validations: any[];
    dependencies: string[];
    buttons: any[];
    presentationLogic: string;
    uiComponents: any[];
  };
  backend: {
    businessLogic: string;
    sqlQueries: any[];
    validations: any[];
    externalCalls: any[];
    dataTransformations: any[];
    dependencies: string[];
  };
  api: {
    endpoints: any[];
    openapiSpec: string;
    securityRequirements: any[];
    dataModels: any[];
    errorHandling: any[];
  };
}

@Component({
  selector: 'app-modules',
  standalone: true,
  imports: [
    CommonModule,
    MatTreeModule,
    MatIconModule,
    MatButtonModule,
    MatCardModule,
    MatDialogModule,
    MatTabsModule,
    MatChipsModule,
    MatProgressSpinnerModule,
    MatMenuModule,
    MatTooltipModule,
    MatDividerModule,
    MatSnackBarModule,
    HttpClientModule
  ],
  templateUrl: './modules.component.html',
  styleUrls: ['./modules.component.scss']
})
export class ModulesComponent implements OnInit {

  private _transformer = (node: ModuleNode, level: number): FlatNode => {
    return {
      expandable: !!node.children && node.children.length > 0,
      name: node.name,
      type: node.type,
      status: node.status,
      level: level,
      path: node.path,
      id: node.id,
      developer: node.developer,
      complexity: node.complexity,
      estimatedHours: node.estimatedHours,
      is_file: node.is_file,
      is_dir: node.is_dir,
      file_count: node.file_count,
      dir_count: node.dir_count,
      size_kb: node.size_kb,
      extension: node.extension,
      line_count: node.line_count,
      char_count: node.char_count,
      function_count: node.function_count,
      functions: node.functions,
      field_count: node.field_count,
      fields: node.fields,
      button_count: node.button_count,
      buttons: node.buttons,
      isLoading: node.isLoading || false
    };
  };

  treeControl = new FlatTreeControl<FlatNode>(
    node => node.level,
    node => node.expandable
  );

  treeFlattener = new MatTreeFlattener(
    this._transformer,
    node => node.level,
    node => node.expandable,
    node => node.children
  );

  dataSource = new MatTreeFlatDataSource(this.treeControl, this.treeFlattener);

  // Datos mock para demostración
  TREE_DATA: ModuleNode[] = [
    {
      name: 'Facturación',
      type: 'module',
      status: 'analyzed',
      path: '/modules/facturacion',
      children: [
        {
          name: 'FACT001.SCR',
          type: 'screen',
          status: 'generated',
          path: '/modules/facturacion/FACT001.SCR',
          id: 'fact001',
          developer: 'Juan Pérez',
          complexity: 3.5,
          estimatedHours: 8
        },
        {
          name: 'FACT002.SCR',
          type: 'screen',
          status: 'analyzed',
          path: '/modules/facturacion/FACT002.SCR',
          id: 'fact002',
          complexity: 2.8,
          estimatedHours: 6
        }
      ]
    },
    {
      name: 'Inventario',
      type: 'module',
      status: 'pending',
      path: '/modules/inventario',
      children: [
        {
          name: 'INV001.SCR',
          type: 'screen',
          status: 'analyzing',
          path: '/modules/inventario/INV001.SCR',
          id: 'inv001'
        },
        {
          name: 'INV002.SCR',
          type: 'screen',
          status: 'pending',
          path: '/modules/inventario/INV002.SCR',
          id: 'inv002'
        }
      ]
    }
  ];

  // Propiedades para datos reales
  isLoading = false;
  errorMessage = '';

  // Propiedades para datos de análisis NSDK
  nsdkAnalyses: NSDKAnalysis[] = [];
  analysisStatus: AnalysisStatus | null = null;
  isLoadingAnalysis = false;
  analysisErrorMessage = '';

  constructor(
    private dialog: MatDialog,
    private modulesService: ModulesService,
    private snackBar: MatSnackBar
  ) {
    // Inicializar con datos vacíos
    this.dataSource.data = [];
  }

  ngOnInit() {
    this.loadModulesFromBackend();
  }

  /**
   * Carga la estructura del repositorio desde el backend
   */
  loadModulesFromBackend() {
    this.isLoading = true;
    this.errorMessage = '';

    // Cargar solo la raíz del repositorio
    this.loadRepositoryRoot();
  }

  /**
   * Carga solo la raíz del repositorio
   */
  loadRepositoryRoot() {
    this.isLoading = true;
    this.errorMessage = '';

    this.modulesService.getRepositoryTree('nsdk-sources').subscribe({
      next: (response) => {
        console.log('=== RESPUESTA COMPLETA DEL BACKEND ===');
        console.log('Response completo:', response);
        console.log('Response.children:', response.children);
        console.log('Response.children.length:', response.children?.length);
        console.log('Response.children[0]:', response.children?.[0]);
        console.log('=== FIN RESPUESTA ===');
        
        // Convertir la respuesta del árbol a ModuleNode[]
        const treeData = this.convertTreeToModuleNodes(response.children || []);
        console.log('TreeData convertido:', treeData);
        console.log('TreeData.length:', treeData.length);
        
        this.dataSource.data = treeData;
        this.isLoading = false;
        
        // Opcionalmente, cargar análisis en segundo plano para estadísticas
        this.loadAnalysisInBackground();
      },
      error: (error) => {
        console.error('Error cargando raíz del repositorio:', error);
        this.errorMessage = 'Error al cargar la estructura del repositorio';
        this.isLoading = false;
      }
    });
  }

  /**
   * Carga el contenido de un directorio cuando se expande
   */
  loadDirectoryContents(node: FlatNode) {
    if (!node.is_dir || node.expandable) {
      return; // Ya está cargado o no es un directorio
    }

    // Marcar como cargando
    node.isLoading = true;
    
    // Obtener la ruta del directorio
    const directoryPath = node.path;
    
    this.modulesService.getDirectoryContents('nsdk-sources', directoryPath).subscribe({
      next: (directoryContents) => {
        console.log(`Contenido del directorio ${directoryPath} cargado:`, directoryContents);
        
        // Convertir el contenido del directorio a ModuleNode[]
        const children = this.convertTreeToModuleNodes(directoryContents);
        
        // Encontrar el nodo en el árbol y actualizar sus hijos
        this.updateNodeChildren(node, children);
        
        // Actualizar el dataSource
        this.dataSource.data = [...this.dataSource.data];
        
        node.isLoading = false;
      },
      error: (error) => {
        console.error(`Error cargando contenido del directorio ${directoryPath}:`, error);
        node.isLoading = false;
        
        // Mostrar error en el nodo
        this.snackBar.open(`Error al cargar el directorio ${node.name}`, 'Cerrar', { duration: 3000 });
      }
    });
  }

  /**
   * Actualiza los hijos de un nodo en el árbol
   */
  private updateNodeChildren(node: FlatNode, children: ModuleNode[]) {
    // Encontrar el índice del nodo en el dataSource
    const nodeIndex = this.dataSource.data.findIndex(n => n.path === node.path);
    if (nodeIndex === -1) return;
    
    // Convertir los hijos a FlatNode[]
    const flatChildren: FlatNode[] = children.map((child, index) => ({
      expandable: !!(child.children && child.children.length > 0),
      name: child.name,
      type: child.type,
      status: child.status,
      level: node.level + 1,
      path: child.path,
      is_file: child.is_file,
      is_dir: child.is_dir,
      file_count: child.file_count,
      dir_count: child.dir_count,
      size_kb: child.size_kb,
      extension: child.extension,
      line_count: child.line_count,
      char_count: child.char_count,
      function_count: child.function_count,
      functions: child.functions || [],
      field_count: child.field_count,
      fields: child.fields || [],
      button_count: child.button_count,
      buttons: child.buttons || [],
      isLoading: false
    }));
    
    // Insertar los hijos después del nodo actual
    const newData = [...this.dataSource.data];
    newData.splice(nodeIndex + 1, 0, ...flatChildren);
    
    // Actualizar el dataSource
    this.dataSource.data = newData;
    
    // Marcar el nodo como expandible
    node.expandable = true;
  }

  /**
   * Convierte un RepositoryTreeNode a ModuleNode[]
   */
  convertTreeToModuleNodes(treeNode: RepositoryTreeNode | RepositoryTreeNode[]): ModuleNode[] {
    const result: ModuleNode[] = [];
    
    // Si es un array, procesar cada elemento
    if (Array.isArray(treeNode)) {
      for (const child of treeNode) {
        const moduleNode: ModuleNode = {
          name: child.name,
          type: child.type,
          path: child.path,
          id: child.id,
          is_file: child.is_file,
          is_dir: child.is_dir,
          file_count: child.file_count,
          dir_count: child.dir_count,
          size_kb: child.size_kb,
          extension: child.extension,
          line_count: child.line_count,
          char_count: child.char_count,
          function_count: child.function_count,
          functions: child.functions || [],
          field_count: child.field_count,
          fields: child.fields || [],
          button_count: child.button_count,
          buttons: child.buttons || [],
          status: 'analyzed',
          children: []
        };
        
        result.push(moduleNode);
      }
    }
    
    return result;
  }

  /**
   * Carga análisis en segundo plano para estadísticas
   */
  loadAnalysisInBackground() {
    this.modulesService.getRepositoryAnalysisStatus('nsdk-sources').subscribe({
      next: (status) => {
        this.analysisStatus = status;
        console.log('Estado del análisis cargado en segundo plano:', status);
      },
      error: (error) => {
        console.log('No se pudo cargar el estado del análisis en segundo plano:', error);
      }
    });
  }

  /**
   * Sincroniza el análisis del repositorio con la base de datos
   * (Método mantenido para uso manual si es necesario)
   */
  syncAnalysisWithDatabase() {
    this.isLoadingAnalysis = true;
    this.analysisErrorMessage = '';

    this.modulesService.syncRepositoryAnalysis('nsdk-sources').subscribe({
      next: (response) => {
        console.log('Análisis sincronizado:', response);
        this.isLoadingAnalysis = false;
        
        // Recargar la raíz después de la sincronización
        this.loadRepositoryRoot();
      },
      error: (error) => {
        console.error('Error sincronizando análisis:', error);
        this.analysisErrorMessage = 'Error al sincronizar el análisis del repositorio';
        this.isLoadingAnalysis = false;
      }
    });
  }

  /**
   * Carga los datos de análisis desde la base de datos
   * (Método mantenido como fallback)
   */
  loadAnalysisFromDatabase() {
    this.isLoading = true;
    this.errorMessage = '';

    // Obtener estado del análisis
    this.modulesService.getRepositoryAnalysisStatus('nsdk-sources').subscribe({
      next: (status) => {
        this.analysisStatus = status;
        console.log('Estado del análisis:', status);
        
        // Cargar todos los análisis
        this.modulesService.getRepositoryAnalysis('nsdk-sources').subscribe({
          next: (response) => {
            this.nsdkAnalyses = response.analyses;
            console.log('Análisis cargados desde BD:', response);
            
            // Convertir a estructura de árbol para el componente
            const treeData = this.convertAnalysesToTreeNodes(response.analyses);
            this.dataSource.data = treeData;
            this.isLoading = false;
          },
          error: (error) => {
            console.error('Error cargando análisis desde BD:', error);
            this.errorMessage = 'Error al cargar análisis desde la base de datos';
            this.isLoading = false;
          }
        });
      },
      error: (error) => {
        console.error('Error obteniendo estado del análisis:', error);
        this.errorMessage = 'Error al obtener el estado del análisis';
        this.isLoading = false;
      }
    });
  }

  /**
   * Convierte análisis NSDK a nodos de árbol
   */
  convertAnalysesToTreeNodes(analyses: NSDKAnalysis[]): ModuleNode[] {
    const treeData: ModuleNode[] = [];
    
    // Agrupar por directorio
    const filesByDirectory = new Map<string, NSDKAnalysis[]>();
    
    for (const analysis of analyses) {
      const pathParts = analysis.file_path.split('/');
      const directory = pathParts.length > 1 ? pathParts.slice(0, -1).join('/') : '.';
      
      if (!filesByDirectory.has(directory)) {
        filesByDirectory.set(directory, []);
      }
      filesByDirectory.get(directory)!.push(analysis);
    }
    
    // Crear nodos de directorio
    for (const [directory, files] of filesByDirectory) {
      if (directory === '.') {
        // Archivos en la raíz
        for (const file of files) {
          const fileNode = this.convertAnalysisToModuleNode(file);
          treeData.push(fileNode);
        }
      } else {
        // Crear nodo de directorio
        const dirNode: ModuleNode = {
          name: directory.split('/').pop() || directory,
          type: 'directory',
          path: directory,
          is_file: false,
          is_dir: true,
          file_count: files.length,
          dir_count: 0,
          children: []
        };
        
        // Agregar archivos como hijos
        for (const file of files) {
          const fileNode = this.convertAnalysisToModuleNode(file);
          dirNode.children!.push(fileNode);
        }
        
        treeData.push(dirNode);
      }
    }
    
    return treeData;
  }

  /**
   * Convierte un análisis NSDK a un nodo del árbol
   */
  convertAnalysisToModuleNode(analysis: NSDKAnalysis): ModuleNode {
    return {
      name: analysis.file_name,
      type: analysis.file_type as any,
      path: analysis.file_path,
      id: analysis.id,
      is_file: true,
      is_dir: false,
      size_kb: analysis.size_kb,
      line_count: analysis.line_count,
      char_count: analysis.char_count,
      function_count: analysis.function_count,
      functions: analysis.functions,
      field_count: analysis.field_count,
      fields: analysis.fields,
      button_count: analysis.button_count,
      buttons: analysis.buttons,
      status: analysis.analysis_status as any,
      children: []
    };
  }

  /**
   * Calcula la complejidad basada en la información del nodo del árbol
   */
  private calculateComplexityFromTreeNode(node: RepositoryTreeNode): number {
    let complexity = 1.0;

    if (node.field_count) complexity += node.field_count * 0.1;
    if (node.button_count) complexity += node.button_count * 0.2;
    if (node.line_count) complexity += node.line_count * 0.01;
    if (node.function_count) complexity += node.function_count * 0.15;

    return Math.min(5.0, Math.round(complexity * 10) / 10);
  }

  /**
   * Estima las horas de desarrollo basado en la información del nodo del árbol
   */
  private estimateHoursFromTreeNode(node: RepositoryTreeNode): number {
    const baseHours = 2;
    const fieldHours = (node.field_count || 0) * 0.5;
    const buttonHours = (node.button_count || 0) * 0.3;
    const functionHours = (node.function_count || 0) * 0.8;
    const complexityHours = this.calculateComplexityFromTreeNode(node) * 1.5;

    return Math.round(baseHours + fieldHours + buttonHours + functionHours + complexityHours);
  }

  /**
   * Obtiene el icono apropiado para el tipo de nodo
   */
  getNodeIcon(type: string): string {
    switch (type) {
      case 'directory':
        return 'folder';
      case 'module':
        return 'code';
      case 'screen':
        return 'visibility';
      case 'include':
        return 'link';
      case 'program':
        return 'terminal';
      case 'config':
        return 'settings';
      case 'document':
        return 'description';
      case 'other':
        return 'insert_drive_file';
      default:
        return 'help';
    }
  }

  /**
   * Extrae el nombre del módulo de la ruta del archivo
   */
  extractModuleNameFromPath(filePath: string): string {
    const parts = filePath.split('/');
    return parts.length > 1 ? parts[1] : 'General';
  }

  /**
   * Calcula la complejidad de una pantalla
   */
  calculateComplexity(screen: NSDKScreen): number {
    let complexity = 1.0;
    complexity += screen.field_count * 0.1;
    complexity += screen.button_count * 0.2;
    complexity += screen.line_count * 0.01;
    return Math.min(5.0, Math.round(complexity * 10) / 10);
  }

  /**
   * Estima las horas de desarrollo
   */
  estimateHours(screen: NSDKScreen): number {
    const baseHours = 2;
    const fieldHours = screen.field_count * 0.5;
    const buttonHours = screen.button_count * 0.3;
    const complexityHours = this.calculateComplexity(screen) * 1.5;
    return Math.round(baseHours + fieldHours + buttonHours + complexityHours);
  }

  hasChild = (_: number, node: FlatNode) => node.expandable;

  getStatusLabel(status: string): string {
    const labels = {
      'pending': 'Pendiente',
      'analyzing': 'Analizando',
      'analyzed': 'Analizado',
      'generated': 'Generado',
      'error': 'Error'
    };
    return labels[status as keyof typeof labels] || status;
  }

  /**
   * Obtiene estadísticas del árbol basadas en análisis de BD
   */
  getTreeStats(): string {
    if (!this.analysisStatus) {
      return 'Cargando estadísticas...';
    }
    
    const db = this.analysisStatus.database_stats;
    const disk = this.analysisStatus.disk_stats;
    
    return `${db.total_files} archivos analizados (${db.analysis_progress.toFixed(1)}% completado) | ${disk.total_files_on_disk} archivos en disco | Estado: ${this.analysisStatus.sync_status === 'in_sync' ? 'Sincronizado' : 'Desincronizado'}`;
  }

  countScreens(nodes: ModuleNode[]): number {
    return nodes.reduce((count, node) => {
      if (node.type === 'screen') count++;
      if (node.children) count += this.countScreens(node.children);
      return count;
    }, 0);
  }

  countScreensByStatus(nodes: ModuleNode[], status: string): number {
    return nodes.reduce((count, node) => {
      if (node.type === 'screen' && node.status === status) count++;
      if (node.children) count += this.countScreensByStatus(node.children, status);
      return count;
    }, 0);
  }

  getModuleScreenCount(node: FlatNode): number {
    const moduleNode = this.TREE_DATA.find(n => n.name === node.name);
    return moduleNode?.children?.length || 0;
  }

  getModuleProgress(node: FlatNode): number {
    const moduleNode = this.TREE_DATA.find(n => n.name === node.name);
    if (!moduleNode?.children) return 0;

    const totalScreens = moduleNode.children.length;
    const completedScreens = moduleNode.children.filter(screen =>
      screen.status === 'generated' || screen.status === 'analyzed'
    ).length;

    return Math.round((completedScreens / totalScreens) * 100);
  }

  /**
   * Refresca los módulos (sincroniza y recarga)
   */
  refreshModules() {
    this.syncAnalysisWithDatabase();
  }

  /**
   * Construye la estructura de directorios en BD
   */
  buildDirectoryTree() {
    console.log('Construyendo estructura de directorios...');
    
    this.modulesService.buildRepositoryTree('nsdk-sources').subscribe({
      next: (response) => {
        console.log('Estructura de directorios construida:', response);
        this.snackBar.open(
          `Estructura de directorios construida. Root ID: ${response.root_directory_id}`,
          'Cerrar',
          { duration: 5000 }
        );
        
        // Recargar módulos después de construir la estructura
        setTimeout(() => {
          this.loadModulesFromBackend();
        }, 2000);
      },
      error: (error) => {
        console.error('Error construyendo estructura de directorios:', error);
        this.snackBar.open(
          'Error al construir la estructura de directorios',
          'Cerrar',
          { duration: 5000 }
        );
      }
    });
  }

  vectorizeCode() {
    console.log('Iniciando vectorización de código...');

    // Por ahora, vectorizamos el repositorio nsdk-sources
    const repoUrl = 'https://repo.plexus.services/jose.diosotero/nsdk-sources.git';

    this.modulesService.vectorizeRepository(repoUrl, 'main').subscribe({
      next: (response) => {
        console.log('Vectorización iniciada:', response);
        this.snackBar.open(
          `Vectorización iniciada. Batch ID: ${response.batch_id}`,
          'Cerrar',
          { duration: 5000 }
        );

        // Recargar módulos después de un delay
        setTimeout(() => {
          this.loadModulesFromBackend();
        }, 3000);
      },
      error: (error) => {
        console.error('Error en vectorización:', error);
        this.snackBar.open(
          'Error al iniciar vectorización',
          'Cerrar',
          { duration: 5000 }
        );
      }
    });
  }

  analyzeScreen(node: FlatNode) {
    console.log(`Analizando pantalla: ${node.name}`);
    node.status = 'analyzing';
    // Simular análisis
    setTimeout(() => {
      node.status = 'analyzed';
    }, 2000);
  }

  viewAnalysis(node: FlatNode) {
    console.log(`Viendo análisis de: ${node.name}`);
    this.openAnalysisModal(node);
  }

  generateCode(node: FlatNode) {
    console.log(`Generando código para: ${node.name}`);
    node.status = 'generated';
  }

  assignDeveloper(node: FlatNode) {
    console.log(`Asignando desarrollador a: ${node.name}`);
  }

  viewCode(node: FlatNode) {
    console.log(`Viendo código de: ${node.name}`);
  }

  exportAnalysis(node: FlatNode) {
    console.log(`Exportando análisis de: ${node.name}`);
  }

  openAnalysisModal(node: FlatNode) {
    const analysisData = this.getMockAnalysisData();

    this.dialog.open(AnalysisModalComponent, {
      width: '90vw',
      height: '90vh',
      data: {
        node: node,
        analysis: analysisData
      }
    });
  }

  getMockAnalysisData(): AnalysisData {
    return {
      frontend: {
        fields: [
          { name: 'codigo', type: 'string', required: true, validation: 'maxLength:10' },
          { name: 'descripcion', type: 'string', required: true, validation: 'maxLength:100' },
          { name: 'precio', type: 'number', required: true, validation: 'min:0' },
          { name: 'stock', type: 'number', required: false, validation: 'min:0' }
        ],
        validations: [
          { field: 'codigo', type: 'required', message: 'El código es obligatorio' },
          { field: 'codigo', type: 'maxLength', value: 10, message: 'Máximo 10 caracteres' },
          { field: 'precio', type: 'min', value: 0, message: 'El precio debe ser mayor a 0' }
        ],
        dependencies: ['@angular/forms', '@angular/material'],
        buttons: [
          { text: 'Guardar', action: 'save', type: 'primary' },
          { text: 'Cancelar', action: 'cancel', type: 'secondary' },
          { text: 'Limpiar', action: 'clear', type: 'secondary' }
        ],
        presentationLogic: 'Formulario de producto con validaciones en tiempo real y botones de acción',
        uiComponents: [
          { type: 'mat-form-field', component: 'MatInputModule' },
          { type: 'mat-button', component: 'MatButtonModule' },
          { type: 'mat-card', component: 'MatCardModule' }
        ]
      },
      backend: {
        businessLogic: 'Validación de negocio para productos: verificar código único, calcular impuestos, validar stock',
        sqlQueries: [
          { type: 'SELECT', query: 'SELECT * FROM productos WHERE codigo = ?', purpose: 'Verificar existencia' },
          { type: 'INSERT', query: 'INSERT INTO productos (codigo, descripcion, precio, stock) VALUES (?, ?, ?, ?)', purpose: 'Crear producto' },
          { type: 'UPDATE', query: 'UPDATE productos SET descripcion = ?, precio = ?, stock = ? WHERE codigo = ?', purpose: 'Actualizar producto' }
        ],
        validations: [
          { field: 'codigo', type: 'unique', table: 'productos', column: 'codigo' },
          { field: 'precio', type: 'range', min: 0, max: 999999.99 },
          { field: 'stock', type: 'range', min: 0, max: 999999 }
        ],
        externalCalls: [
          { service: 'TaxService', method: 'calculateTax', async: true, purpose: 'Calcular impuestos' },
          { service: 'InventoryService', method: 'checkStock', async: false, purpose: 'Verificar stock disponible' }
        ],
        dataTransformations: [
          { from: 'string', to: 'uppercase', field: 'codigo' },
          { from: 'number', to: 'currency', field: 'precio', format: 'USD' },
          { from: 'date', to: 'string', field: 'fecha_creacion', format: 'YYYY-MM-DD' }
        ],
        dependencies: ['sqlalchemy', 'pydantic', 'fastapi']
      },
      api: {
        endpoints: [
          { method: 'GET', path: '/api/productos', description: 'Listar productos' },
          { method: 'GET', path: '/api/productos/{id}', description: 'Obtener producto por ID' },
          { method: 'POST', path: '/api/productos', description: 'Crear producto' },
          { method: 'PUT', path: '/api/productos/{id}', description: 'Actualizar producto' },
          { method: 'DELETE', path: '/api/productos/{id}', description: 'Eliminar producto' }
        ],
        openapiSpec: `
          openapi: 3.0.0
          info:
            title: API de Productos
            version: 1.0.0
          paths:
            /api/productos:
              get:
                summary: Listar productos
                responses:
                  '200':
                    description: Lista de productos
              post:
                summary: Crear producto
                requestBody:
                  required: true
                  content:
                    application/json:
                      schema:
                        $ref: '#/components/schemas/Producto'
        `,
        securityRequirements: [
          { type: 'JWT', scope: 'productos:read' },
          { type: 'JWT', scope: 'productos:write' }
        ],
        dataModels: [
          { name: 'Producto', fields: ['id', 'codigo', 'descripcion', 'precio', 'stock', 'fecha_creacion'] },
          { name: 'ProductoCreate', fields: ['codigo', 'descripcion', 'precio', 'stock'] },
          { name: 'ProductoUpdate', fields: ['descripcion', 'precio', 'stock'] }
        ],
        errorHandling: [
          { code: 400, message: 'Datos inválidos', type: 'ValidationError' },
          { code: 404, message: 'Producto no encontrado', type: 'NotFoundError' },
          { code: 409, message: 'Código de producto duplicado', type: 'ConflictError' },
          { code: 500, message: 'Error interno del servidor', type: 'InternalServerError' }
        ]
      }
    };
  }
}

// Componente del modal de análisis
import { Inject } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';

@Component({
  selector: 'app-analysis-modal',
  standalone: true,
  imports: [
    CommonModule,
    MatTabsModule,
    MatCardModule,
    MatChipsModule,
    MatButtonModule,
    MatIconModule,
    MatDividerModule
  ],
  template: `
    <div class="analysis-modal">
      <div class="modal-header">
        <h2>Análisis de {{ data.node.name }}</h2>
        <button mat-icon-button (click)="dialogRef.close()">
          <mat-icon>close</mat-icon>
        </button>
      </div>
      
      <div class="modal-content">
        <mat-tab-group>
          <!-- Frontend Tab -->
          <mat-tab label="Frontend">
            <div class="tab-content">
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Campos del Formulario</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <div class="field-item" *ngFor="let field of data.analysis.frontend.fields">
                    <div class="field-header">
                      <strong>{{ field.name }}</strong>
                      <mat-chip [color]="field.required ? 'primary' : 'default'">
                        {{ field.type }}
                      </mat-chip>
                    </div>
                    <p class="field-validation">{{ field.validation }}</p>
                  </div>
                </mat-card-content>
              </mat-card>
              
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Validaciones</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <div class="validation-item" *ngFor="let validation of data.analysis.frontend.validations">
                    <mat-chip color="warn">{{ validation.field }}</mat-chip>
                    <span>{{ validation.message }}</span>
                  </div>
                </mat-card-content>
              </mat-card>
              
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Botones</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <div class="button-item" *ngFor="let button of data.analysis.frontend.buttons">
                    <mat-chip [color]="button.type === 'primary' ? 'primary' : 'default'">
                      {{ button.text }}
                    </mat-chip>
                    <span>{{ button.action }}</span>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>
          </mat-tab>
          
          <!-- Backend Tab -->
          <mat-tab label="Backend">
            <div class="tab-content">
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Lógica de Negocio</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <p>{{ data.analysis.backend.businessLogic }}</p>
                </mat-card-content>
              </mat-card>
              
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Consultas SQL</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <div class="sql-item" *ngFor="let query of data.analysis.backend.sqlQueries">
                    <div class="query-header">
                      <mat-chip [color]="getSqlTypeColor(query.type)">{{ query.type }}</mat-chip>
                      <span>{{ query.purpose }}</span>
                    </div>
                    <pre class="query-sql">{{ query.query }}</pre>
                  </div>
                </mat-card-content>
              </mat-card>
              
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Llamadas Externas</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <div class="call-item" *ngFor="let call of data.analysis.backend.externalCalls">
                    <div class="call-header">
                      <strong>{{ call.service }}</strong>
                      <mat-chip [color]="call.async ? 'warn' : 'default'">
                        {{ call.async ? 'Async' : 'Sync' }}
                      </mat-chip>
                    </div>
                    <p>{{ call.method }} - {{ call.purpose }}</p>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>
          </mat-tab>
          
          <!-- API Tab -->
          <mat-tab label="API">
            <div class="tab-content">
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Endpoints</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <div class="endpoint-item" *ngFor="let endpoint of data.analysis.api.endpoints">
                    <div class="endpoint-header">
                      <mat-chip [color]="getMethodColor(endpoint.method)">{{ endpoint.method }}</mat-chip>
                      <code>{{ endpoint.path }}</code>
                    </div>
                    <p>{{ endpoint.description }}</p>
                  </div>
                </mat-card-content>
              </mat-card>
              
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Modelos de Datos</mat-card-title>
                </mat-card-header>
                <mat-card-content>
                  <div class="model-item" *ngFor="let model of data.analysis.api.dataModels">
                    <h4>{{ model.name }}</h4>
                    <div class="model-fields">
                      <mat-chip *ngFor="let field of model.fields" color="accent">{{ field }}</mat-chip>
                    </div>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>
          </mat-tab>
        </mat-tab-group>
      </div>
      
      <div class="modal-actions">
        <button mat-raised-button color="primary" (click)="generateCode()">
          <mat-icon>code</mat-icon>
          Generar Código
        </button>
        <button mat-raised-button (click)="exportAnalysis()">
          <mat-icon>download</mat-icon>
          Exportar Análisis
        </button>
        <button mat-button (click)="dialogRef.close()">Cerrar</button>
      </div>
    </div>
  `,
  styles: [`
    .analysis-modal {
      height: 100%;
      display: flex;
      flex-direction: column;
    }
    
    .modal-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 20px;
      border-bottom: 1px solid #eee;
    }
    
    .modal-header h2 {
      margin: 0;
    }
    
    .modal-content {
      flex: 1;
      overflow: auto;
      padding: 20px;
    }
    
    .tab-content {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    
    .field-item, .validation-item, .button-item, .sql-item, .call-item, .endpoint-item, .model-item {
      margin-bottom: 15px;
      padding: 10px;
      border: 1px solid #eee;
      border-radius: 4px;
    }
    
    .field-header, .query-header, .call-header, .endpoint-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 5px;
    }
    
    .field-validation {
      margin: 5px 0 0 0;
      color: #666;
      font-size: 12px;
    }
    
    .query-sql {
      background-color: #f5f5f5;
      padding: 10px;
      border-radius: 4px;
      font-family: monospace;
      margin: 10px 0 0 0;
    }
    
    .model-fields {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      margin-top: 10px;
    }
    
    .modal-actions {
      display: flex;
      gap: 10px;
      padding: 20px;
      border-top: 1px solid #eee;
      justify-content: flex-end;
    }
  `]
})
export class AnalysisModalComponent {
  constructor(
    public dialogRef: MatDialogRef<AnalysisModalComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) { }

  getSqlTypeColor(type: string): string {
    const colors = {
      'SELECT': 'primary',
      'INSERT': 'accent',
      'UPDATE': 'warn',
      'DELETE': 'warn'
    };
    return colors[type as keyof typeof colors] || 'default';
  }

  getMethodColor(method: string): string {
    const colors = {
      'GET': 'primary',
      'POST': 'accent',
      'PUT': 'warn',
      'DELETE': 'warn'
    };
    return colors[method as keyof typeof colors] || 'default';
  }

  generateCode() {
    console.log('Generando código...');
  }

  exportAnalysis() {
    console.log('Exportando análisis...');
  }
}