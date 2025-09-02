import { CollectionViewer, DataSource, SelectionChange } from '@angular/cdk/collections';
import { FlatTreeControl } from '@angular/cdk/tree';
import { CommonModule } from '@angular/common';
import { HttpClient, HttpClientModule } from '@angular/common/http';
import { Component, Injectable, OnInit } from '@angular/core';
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
import { MatTreeModule } from '@angular/material/tree';
import { BehaviorSubject, firstValueFrom, merge, Observable } from 'rxjs';
import { map } from 'rxjs/operators';

import { AIAnalysisModalComponent } from './modals/ai-analysis-modal.component';
import { FileViewerModalComponent } from './modals/file-viewer-modal.component';
import { AnalysisStatus, ModulesService, NSDKAnalysis, NSDKScreen, RepositoryTreeNode } from './modules.service';

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
  isLoading?: boolean;
  expandable?: boolean;
  level?: number;
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
  isLoading?: boolean;
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

/**
 * DynamicDataSource personalizado que maneja correctamente la expansión/contracción
 */
@Injectable()
export class DynamicDataSource extends DataSource<FlatNode> {
  dataChange: BehaviorSubject<FlatNode[]> = new BehaviorSubject<FlatNode[]>([]);
  private expandedNodes = new Set<string>(); // Mantener registro de nodos expandidos
  private isLoadingChildren = false; // Bandera para evitar eventos durante la carga

  get data(): FlatNode[] { return this.dataChange.value; }
  set data(value: FlatNode[]) {
    this.treeControl.dataNodes = value;
    this.dataChange.next(value);
  }

  constructor(private treeControl: FlatTreeControl<FlatNode>,
    private modulesService: ModulesService) {
    super();
  }

  connect(collectionViewer: CollectionViewer): Observable<FlatNode[]> {
    this.treeControl.expansionModel.changed.subscribe(change => {
      if ((change as SelectionChange<FlatNode>).added ||
        (change as SelectionChange<FlatNode>).removed) {
        this.handleTreeControl(change as SelectionChange<FlatNode>);
      }
    });

    return merge(collectionViewer.viewChange, this.dataChange).pipe(map(() => this.data));
  }

  disconnect(collectionViewer: CollectionViewer): void {
    // Cleanup cuando se desconecta
  }

  /** Handle expand/collapse behaviors */
  handleTreeControl(change: SelectionChange<FlatNode>) {
    console.log('=== handleTreeControl ===');
    console.log('Change:', change);
    console.log('Added:', change.added);
    console.log('Removed:', change.removed);
    console.log('isLoadingChildren:', this.isLoadingChildren);

    // Si estamos cargando hijos, ignorar eventos de contracción
    if (this.isLoadingChildren && change.removed && change.removed.length > 0) {
      console.log('Ignorando evento de contracción durante carga de hijos');
      return;
    }

    if (change.added) {
      change.added.forEach((node) => {
        console.log(`Expandiendo nodo: ${node.name} (ID: ${node.id})`);
        this.expandedNodes.add(node.id || node.path); // Registrar como expandido
        this.toggleNode(node, true);
      });
    }
    if (change.removed) {
      change.removed.reverse().forEach((node) => {
        console.log(`Contrayendo nodo: ${node.name} (ID: ${node.id})`);
        this.expandedNodes.delete(node.id || node.path); // Remover de expandidos
        this.toggleNode(node, false);
      });
    }
  }

  /**
   * Toggle the node, remove from display list
   */
  toggleNode(node: FlatNode, expand: boolean) {
    console.log(`=== toggleNode ===`);
    console.log(`Nodo: ${node.name}, Expand: ${expand}, ID: ${node.id}`);
    console.log(`TreeControl isExpanded: ${this.treeControl.isExpanded(node)}`);

    if (!node.is_dir || !node.id) {
      console.log('No es directorio o no tiene ID, saliendo...');
      return;
    }

    const index = this.data.indexOf(node);
    if (index < 0) {
      console.log('No se encontró el nodo en el dataSource');
      return;
    }

    // Verificar si ya tiene hijos cargados - buscar hijos directos del siguiente nivel
    const hasLoadedChildren = this.data.some(n =>
      n.level === node.level + 1 &&
      n.path.startsWith(node.path + '\\') && // Usar backslash para Windows paths
      this.isDirectChild(node.path, n.path)
    );

    console.log(`Has loaded children: ${hasLoadedChildren}`);
    console.log(`Node path: ${node.path}, level: ${node.level}`);

    if (expand) {
      if (hasLoadedChildren) {
        console.log('Ya tiene hijos cargados, contraer...');
        // Si ya tiene hijos cargados, contraer el nodo
        this.collapseNode(node, index);
        // Remover del registro de expandidos
        this.expandedNodes.delete(node.id || node.path);
        return;
      }

      console.log('Cargando hijos del directorio...');
      node.isLoading = true;
      this.isLoadingChildren = true; // Marcar que estamos cargando

      // Cargar hijos del directorio
      this.modulesService.getDirectoryContents('nsdk-sources', node.id).subscribe({
        next: (directoryContents) => {
          console.log(`Hijos cargados para ${node.name}:`, directoryContents);
          const children = this.convertToFlatNodes(directoryContents, node.level + 1);

          // Encontrar la posición correcta para insertar los hijos
          const insertIndex = this.findInsertPosition(node, index);
          console.log(`Insertando ${children.length} hijos en posición ${insertIndex}`);

          // Insertar los hijos en la posición correcta
          this.data.splice(insertIndex, 0, ...children);

          // Marcar el nodo como expandible si tiene hijos
          node.expandable = children.length > 0;

          // Notificar el cambio
          this.dataChange.next(this.data);
          node.isLoading = false;
          this.isLoadingChildren = false; // Marcar que terminamos de cargar

          console.log(`Nodo ${node.name} expandido con ${children.length} hijos`);
        },
        error: (error) => {
          console.error(`Error cargando contenido del directorio ${node.name}:`, error);
          node.isLoading = false;
          this.isLoadingChildren = false; // Marcar que terminamos de cargar
        }
      });
    } else {
      console.log('Contrayendo nodo...');
      // Contraer el nodo
      this.collapseNode(node, index);
    }
  }

  /**
   * Verifica si un nodo es hijo directo de otro
   */
  private isDirectChild(parentPath: string, childPath: string): boolean {
    // Normalizar paths para Windows
    const normalizedParent = parentPath.replace(/\\/g, '/');
    const normalizedChild = childPath.replace(/\\/g, '/');

    // Verificar que el hijo empiece con el path del padre + '/'
    if (!normalizedChild.startsWith(normalizedParent + '/')) {
      return false;
    }

    // Verificar que no haya más niveles de directorio
    const relativePath = normalizedChild.substring(normalizedParent.length + 1);
    return !relativePath.includes('/');
  }

  /**
   * Encuentra la posición correcta para insertar los hijos
   */
  private findInsertPosition(node: FlatNode, nodeIndex: number): number {
    // Buscar el último hijo directo o el siguiente nodo del mismo nivel
    for (let i = nodeIndex + 1; i < this.data.length; i++) {
      const currentNode = this.data[i];

      // Si encontramos un nodo del mismo nivel o superior, insertar antes
      if (currentNode.level <= node.level) {
        return i;
      }

      // Si es un hijo directo, continuar buscando
      if (this.isDirectChild(node.path, currentNode.path)) {
        continue;
      }

      // Si encontramos un nodo que no es hijo directo, insertar antes
      if (currentNode.level > node.level) {
        return i;
      }
    }

    // Si no encontramos nada, insertar al final
    return this.data.length;
  }

  /**
   * Contrae un nodo eliminando todos sus hijos
   */
  private collapseNode(node: FlatNode, index: number) {
    console.log(`Contrayendo nodo ${node.name} desde índice ${index}`);

    // Encontrar todos los hijos y nietos del directorio
    const childrenToRemove: number[] = [];

    for (let i = index + 1; i < this.data.length; i++) {
      const currentNode = this.data[i];

      // Si encontramos un nodo del mismo nivel o superior, paramos
      if (currentNode.level <= node.level) {
        console.log(`Parando en índice ${i}, nodo ${currentNode.name} del mismo nivel o superior`);
        break;
      }

      // Si es un hijo directo o descendiente del directorio actual, marcarlo para eliminar
      if (this.isDescendant(node.path, currentNode.path)) {
        childrenToRemove.push(i);
        console.log(`Marcando para eliminar: ${currentNode.name} (índice ${i})`);
      }
    }

    console.log(`Eliminando ${childrenToRemove.length} nodos hijos`);

    // Eliminar los hijos en orden inverso para no afectar los índices
    for (let i = childrenToRemove.length - 1; i >= 0; i--) {
      this.data.splice(childrenToRemove[i], 1);
    }

    // Notificar el cambio
    this.dataChange.next(this.data);
  }

  /**
   * Verifica si un nodo es descendiente de otro
   */
  private isDescendant(parentPath: string, childPath: string): boolean {
    // Normalizar paths para Windows
    const normalizedParent = parentPath.replace(/\\/g, '/');
    const normalizedChild = childPath.replace(/\\/g, '/');

    // Verificar que el hijo empiece con el path del padre + '/'
    return normalizedChild.startsWith(normalizedParent + '/');
  }

  /**
   * Convierte RepositoryTreeNode[] a FlatNode[]
   */
  private convertToFlatNodes(treeNode: RepositoryTreeNode[], level: number): FlatNode[] {
    return treeNode.map(child => {
      // DEBUG: Log para ver qué está llegando
      if (child.name === 'd_poliza.scr') {
        console.log('🔍 DEBUG d_poliza.scr (convertToFlatNodes):', {
          name: child.name,
          analysis_status: child.analysis_status,
          analysis_date: child.analysis_date,
          is_file: child.is_file,
          type: child.type
        });
      }

      return {
        expandable: child.is_dir && (child.expandable === true || (((child.dir_count || 0) + (child.file_count || 0)) > 0)),
        name: child.name,
        type: child.type,
        status: (child.analysis_status as 'pending' | 'analyzing' | 'analyzed' | 'generated' | 'error') || 'pending', // ← USAR EL CAMPO DEL ÁRBOL
        level: level,
        path: child.path,
        id: child.id,
        developer: undefined, // RepositoryTreeNode no tiene esta propiedad
        complexity: undefined, // RepositoryTreeNode no tiene esta propiedad
        estimatedHours: undefined, // RepositoryTreeNode no tiene esta propiedad
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
      };
    });
  }
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

  treeControl = new FlatTreeControl<FlatNode>(
    node => node.level,
    node => node.expandable
  );

  dataSource: DynamicDataSource;

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
    private snackBar: MatSnackBar,
    private http: HttpClient
  ) {
    // Inicializar con DynamicDataSource
    this.dataSource = new DynamicDataSource(this.treeControl, this.modulesService);
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
      next: (response: any) => {
        console.log('=== RESPUESTA COMPLETA DEL BACKEND ===');
        console.log('Response completo:', response);
        console.log('Response.children:', response.children);
        console.log('Response.children.length:', response.children?.length);
        console.log('Response.children[0]:', response.children?.[0]);
        console.log('=== FIN RESPUESTA ===');

        // Convertir la respuesta del árbol a FlatNode[]
        const treeData = this.convertTreeToFlatNodes(response.children || []);
        console.log('TreeData convertido:', treeData);
        console.log('TreeData.length:', treeData.length);

        this.dataSource.data = treeData;
        this.isLoading = false;

        // Opcionalmente, cargar análisis en segundo plano para estadísticas
        this.loadAnalysisInBackground();
      },
      error: (error: any) => {
        console.error('Error cargando raíz del repositorio:', error);
        this.errorMessage = 'Error al cargar la estructura del repositorio';
        this.isLoading = false;
      }
    });
  }

  /**
   * Convierte RepositoryTreeNode[] a FlatNode[]
   */
  convertTreeToFlatNodes(treeNode: RepositoryTreeNode[]): FlatNode[] {
    return treeNode.map(child => ({
      expandable: child.is_dir && (child.expandable === true || (((child.dir_count || 0) + (child.file_count || 0)) > 0)),
      name: child.name,
      type: child.type,
      status: child.is_file && child.id ? this.getAnalysisStatus(child.id) : undefined,
      level: 0,
      path: child.path,
      id: child.id,
      developer: undefined, // RepositoryTreeNode no tiene esta propiedad
      complexity: undefined, // RepositoryTreeNode no tiene esta propiedad
      estimatedHours: undefined, // RepositoryTreeNode no tiene esta propiedad
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
  }

  /**
   * Obtiene el estado de análisis de un archivo específico
   */
  private getAnalysisStatus(fileId: string): 'pending' | 'analyzing' | 'analyzed' | 'generated' | 'error' {
    // Buscar en los análisis cargados
    const analysis = this.nsdkAnalyses.find(a => a.id === fileId);
    if (analysis) {
      return (analysis.analysis_status as 'pending' | 'analyzing' | 'analyzed' | 'generated' | 'error') || 'pending';
    }
    return 'pending';
  }

  /**
 * Carga análisis en segundo plano para estadísticas
 */
  loadAnalysisInBackground() {
    // Cargar estado general del análisis
    this.modulesService.getRepositoryAnalysisStatus('nsdk-sources').subscribe({
      next: (status: any) => {
        this.analysisStatus = status;
        console.log('Estado del análisis cargado en segundo plano:', status);
      },
      error: (error: any) => {
        console.log('No se pudo cargar el estado del análisis en segundo plano:', error);
      }
    });

    // Cargar análisis individuales de archivos
    this.modulesService.getRepositoryAnalysis('nsdk-sources').subscribe({
      next: (response: any) => {
        this.nsdkAnalyses = response.analyses || [];
        console.log('Análisis individuales cargados:', this.nsdkAnalyses.length);

        // Actualizar el estado de los nodos en el árbol
        this.updateTreeNodesStatus();
      },
      error: (error: any) => {
        console.log('No se pudieron cargar los análisis individuales:', error);
      }
    });
  }

  /**
 * Actualiza el estado de los nodos en el árbol basado en los análisis cargados
 */
  private updateTreeNodesStatus() {
    const currentData = this.dataSource.data;
    const updatedData = currentData.map(node => {
      if (node.is_file && node.id) {
        const analysis = this.nsdkAnalyses.find(a => a.id === node.id);
        if (analysis) {
          return {
            ...node,
            status: (analysis.analysis_status as 'pending' | 'analyzing' | 'analyzed' | 'generated' | 'error') || 'pending'
          };
        }
      }
      return node;
    });

    this.dataSource.data = updatedData;
  }

  /**
   * Sincroniza el análisis del repositorio con la base de datos
   * (Método mantenido para uso manual si es necesario)
   */
  syncAnalysisWithDatabase() {
    this.isLoadingAnalysis = true;
    this.analysisErrorMessage = '';

    this.modulesService.syncRepositoryAnalysis('nsdk-sources').subscribe({
      next: (response: any) => {
        console.log('Análisis sincronizado:', response);
        this.isLoadingAnalysis = false;

        // Recargar la raíz después de la sincronización
        this.loadRepositoryRoot();
      },
      error: (error: any) => {
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
      next: (status: any) => {
        this.analysisStatus = status;
        console.log('Estado del análisis:', status);

        // Cargar todos los análisis
        this.modulesService.getRepositoryAnalysis('nsdk-sources').subscribe({
          next: (response: any) => {
            this.nsdkAnalyses = response.analyses;
            console.log('Análisis cargados desde BD:', response);

            // Convertir a estructura de árbol para el componente
            const treeData = this.convertAnalysesToTreeNodes(response.analyses);
            // Convertir ModuleNode[] a FlatNode[] para el dataSource
            const flatTreeData = this.convertModuleNodesToFlatNodes(treeData);
            this.dataSource.data = flatTreeData;
            this.isLoading = false;
          },
          error: (error: any) => {
            console.error('Error cargando análisis desde BD:', error);
            this.errorMessage = 'Error al cargar análisis desde la base de datos';
            this.isLoading = false;
          }
        });
      },
      error: (error: any) => {
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
   * Convierte ModuleNode[] a FlatNode[] para el dataSource
   */
  private convertModuleNodesToFlatNodes(nodes: ModuleNode[]): FlatNode[] {
    const flatNodes: FlatNode[] = [];

    const flattenNodes = (nodeList: ModuleNode[], level: number) => {
      for (const node of nodeList) {
        flatNodes.push({
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
          functions: node.functions || [],
          field_count: node.field_count,
          fields: node.fields || [],
          button_count: node.button_count,
          buttons: node.buttons || [],
          isLoading: node.isLoading || false
        });

        // Recursivamente procesar hijos
        if (node.children && node.children.length > 0) {
          flattenNodes(node.children, level + 1);
        }
      }
    };

    flattenNodes(nodes, 0);
    return flatNodes;
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
   * Determina si un nodo representa un fichero .SCR (case-insensitive)
   */
  isScrFile(node: FlatNode): boolean {
    if (!node || !node.is_file) return false;
    if (node.extension && typeof node.extension === 'string') {
      if (node.extension.toUpperCase() === 'SCR') return true;
    }
    if (node.name && typeof node.name === 'string') {
      return node.name.toUpperCase().endsWith('.SCR');
    }
    return false;
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
      next: (response: any) => {
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
      error: (error: any) => {
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
      next: (response: any) => {
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
      error: (error: any) => {
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
    console.log('=== ANALIZAR ARCHIVO ===');
    console.log('Nodo:', node);
    console.log('ID del nodo:', node.id);
    console.log('Path del nodo:', node.path);
    console.log('Nombre del nodo:', node.name);

    if (!node.id) {
      console.error('ID no disponible para análisis');
      this.snackBar.open(
        `Error: El archivo ${node.name} no tiene ID asignado. Esto indica que no está registrado en la base de datos.`,
        'Cerrar',
        { duration: 5000 }
      );
      return;
    }

    this.performAnalysis(node);
  }

  private performAnalysis(node: FlatNode) {
    if (!node.id) {
      console.error('ID no disponible para análisis');
      this.snackBar.open('Error: ID de archivo no disponible para análisis', 'Cerrar', { duration: 3000 });
      return;
    }

    console.log(`Iniciando análisis IA para: ${node.name}`);
    node.status = 'analyzing';

    const repoName = 'nsdk-sources';
    this.modulesService.analyzeFileWithAI(repoName, node.id).subscribe({
      next: (response: any) => {
        console.log('Análisis IA completado:', response);
        node.status = 'analyzed';

        // Actualizar la lista de análisis
        const existingIndex = this.nsdkAnalyses.findIndex(a => a.id === node.id);
        if (existingIndex >= 0) {
          this.nsdkAnalyses[existingIndex].analysis_status = 'analyzed';
        } else {
          // Agregar nuevo análisis si no existe
          this.nsdkAnalyses.push({
            id: node.id,
            file_name: node.name,
            analysis_status: 'analyzed'
          } as NSDKAnalysis);
        }

        this.snackBar.open(
          `Análisis IA completado para ${node.name}`,
          'Cerrar',
          { duration: 3000 }
        );
      },
      error: (error: any) => {
        console.error('Error en análisis IA:', error);
        node.status = 'error';
        this.snackBar.open(
          `Error en análisis IA: ${error.error?.detail || error.message}`,
          'Cerrar',
          { duration: 5000 }
        );
      }
    });
  }

  viewAnalysis(node: FlatNode) {
    if (!node.id) {
      this.snackBar.open('Error: ID de archivo no disponible', 'Cerrar', { duration: 3000 });
      return;
    }

    console.log(`Obteniendo análisis IA de: ${node.name}`);
    const repoName = 'nsdk-sources';

    this.modulesService.getAIAnalysisResult(repoName, node.id).subscribe({
      next: (response: any) => {
        console.log('Análisis IA obtenido:', response);
        console.log('Estructura de response.analysis:', response.analysis);

        // Usar el AIAnalysisModalComponent para mostrar datos reales de IA
        this.dialog.open(AIAnalysisModalComponent, {
          width: '95vw',
          height: '95vh',
          data: {
            node: {
              ...node,
              repository_name: repoName  // Agregar el nombre del repositorio
            },
            analysis: response.analysis
          }
        });
      },
      error: (error: any) => {
        console.error('Error obteniendo análisis IA:', error);
        if (error.status === 404) {
          this.snackBar.open(
            `No se encontró análisis IA para ${node.name}. Analiza el archivo primero.`,
            'Cerrar',
            { duration: 5000 }
          );
        } else {
          this.snackBar.open(
            `Error obteniendo análisis IA: ${error.error?.detail || error.message}`,
            'Cerrar',
            { duration: 5000 }
          );
        }
      }
    });
  }



  assignDeveloper(node: FlatNode) {
    console.log(`Asignando desarrollador a: ${node.name}`);
  }

  viewCode(node: FlatNode) {
    if (!node.is_file) return;
    const repoName = 'nsdk-sources';
    // Intentar por id si existe; si no, por path
    const options: any = {};
    if (node.id) options.fileId = node.id;
    else if (node.path) options.filePath = node.path;

    this.modulesService.getFileContent(repoName, options).subscribe({
      next: (resp: any) => {
        this.dialog.open(FileViewerModalComponent, {
          width: '90vw',
          height: '90vh',
          data: {
            node,
            content: resp.content_text || '',
            path: resp.path,
            size: resp.size_bytes
          }
        });
      },
      error: (err: any) => {
        console.error('Error obteniendo contenido del fichero', err);
        this.snackBar.open('No se pudo cargar el contenido del fichero', 'Cerrar', { duration: 4000 });
      }
    });
  }

  exportAnalysis(node: FlatNode) {
    console.log(`Exportando análisis de: ${node.name}`);
  }



  async generateCode(node: any) {
    try {
      console.log('Iniciando generación de código para:', node.name);

      // Mostrar indicador de carga
      node.status = 'generating';

      // Llamar al endpoint de generación de código
      const response = await firstValueFrom(
        this.http.post<{ success: boolean, branch_name: string, message?: string }>(
          `http://localhost:8000/repositories/nsdk-sources/files/${node.id}/generate-code`,
          null
        )
      );

      if (response.success) {
        console.log('Código generado exitosamente:', response);

        // Mostrar mensaje de éxito
        this.snackBar.open(
          `Código generado exitosamente en rama ${response.branch_name}`,
          'Cerrar',
          { duration: 5000 }
        );

        // Actualizar estado del nodo
        node.status = 'generated';

      } else {
        throw new Error(response.message || 'Error generando código');
      }

    } catch (error: any) {
      console.error('Error generando código:', error);

      // Mostrar mensaje de error
      this.snackBar.open(
        `Error generando código: ${error?.message || error}`,
        'Cerrar',
        { duration: 5000 }
      );

      // Revertir estado del nodo
      node.status = 'analyzed';

    } finally {
      // Asegurar que el estado se actualice
      this.refreshModules();
    }
  }
}






