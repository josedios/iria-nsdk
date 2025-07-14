import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatTreeModule } from '@angular/material/tree';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatDialogModule, MatDialog } from '@angular/material/dialog';
import { MatTabsModule } from '@angular/material/tabs';
import { MatChipsModule } from '@angular/material/chips';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatMenuModule } from '@angular/material/menu';
import { MatTooltipModule } from '@angular/material/tooltip';
import { FlatTreeControl } from '@angular/cdk/tree';
import { MatTreeFlatDataSource, MatTreeFlattener } from '@angular/material/tree';

interface ModuleNode {
  name: string;
  type: 'module' | 'screen';
  status: 'pending' | 'analyzing' | 'analyzed' | 'generated' | 'error';
  path: string;
  children?: ModuleNode[];
  id?: string;
  developer?: string;
  complexity?: number;
  estimatedHours?: number;
}

interface FlatNode {
  expandable: boolean;
  name: string;
  type: 'module' | 'screen';
  status: 'pending' | 'analyzing' | 'analyzed' | 'generated' | 'error';
  level: number;
  path: string;
  id?: string;
  developer?: string;
  complexity?: number;
  estimatedHours?: number;
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
    MatTooltipModule
  ],
  template: `
    <div class="modules-container">
      <div class="modules-header">
        <h1>Explorador de Módulos</h1>
        <div class="header-actions">
          <button mat-raised-button color="primary" (click)="refreshModules()">
            <mat-icon>refresh</mat-icon>
            Actualizar
          </button>
          <button mat-raised-button color="accent" (click)="vectorizeCode()">
            <mat-icon>upload</mat-icon>
            Vectorizar Código
          </button>
        </div>
      </div>
      
      <div class="modules-content">
        <mat-card class="modules-tree-card">
          <mat-card-header>
            <mat-card-title>Árbol de Módulos y Pantallas</mat-card-title>
            <mat-card-subtitle>{{ getTreeStats() }}</mat-card-subtitle>
          </mat-card-header>
          <mat-card-content>
            <mat-tree [dataSource]="dataSource" [treeControl]="treeControl">
              <mat-tree-node *matTreeNodeDef="let node" matTreeNodePadding>
                <div class="tree-node">
                  <div class="node-content">
                    <mat-icon class="node-icon" [class]="'node-type-' + node.type">
                      {{ node.type === 'module' ? 'folder' : 'visibility' }}
                    </mat-icon>
                    <span class="node-name">{{ node.name }}</span>
                    <mat-chip class="status-chip" [class]="'status-' + node.status">
                      {{ getStatusLabel(node.status) }}
                    </mat-chip>
                  </div>
                  
                  <div class="node-actions" *ngIf="node.type === 'screen'">
                    <button mat-icon-button 
                            [matTooltip]="'Analizar pantalla'" 
                            (click)="analyzeScreen(node)"
                            [disabled]="node.status === 'analyzing'">
                      <mat-icon>analytics</mat-icon>
                    </button>
                    <button mat-icon-button 
                            [matTooltip]="'Ver análisis'" 
                            (click)="viewAnalysis(node)"
                            [disabled]="node.status === 'pending'">
                      <mat-icon>visibility</mat-icon>
                    </button>
                    <button mat-icon-button 
                            [matTooltip]="'Generar código'" 
                            (click)="generateCode(node)"
                            [disabled]="node.status !== 'analyzed'">
                      <mat-icon>code</mat-icon>
                    </button>
                    <button mat-icon-button 
                            [matMenuTriggerFor]="menu" 
                            [matTooltip]="'Más opciones'">
                      <mat-icon>more_vert</mat-icon>
                    </button>
                    
                    <mat-menu #menu="matMenu">
                      <button mat-menu-item (click)="assignDeveloper(node)">
                        <mat-icon>person</mat-icon>
                        Asignar Desarrollador
                      </button>
                      <button mat-menu-item (click)="viewCode(node)">
                        <mat-icon>code</mat-icon>
                        Ver Código SCR
                      </button>
                      <button mat-menu-item (click)="exportAnalysis(node)">
                        <mat-icon>download</mat-icon>
                        Exportar Análisis
                      </button>
                    </mat-menu>
                  </div>
                </div>
              </mat-tree-node>
              
              <mat-tree-node *matTreeNodeDef="let node;when: hasChild" matTreeNodePadding>
                <div class="tree-node">
                  <div class="node-content">
                    <button mat-icon-button matTreeNodeToggle
                            [attr.aria-label]="'Toggle ' + node.name">
                      <mat-icon class="mat-icon-rtl-mirror">
                        {{ treeControl.isExpanded(node) ? 'expand_more' : 'chevron_right' }}
                      </mat-icon>
                    </button>
                    <mat-icon class="node-icon" [class]="'node-type-' + node.type">
                      {{ node.type === 'module' ? 'folder' : 'visibility' }}
                    </mat-icon>
                    <span class="node-name">{{ node.name }}</span>
                    <mat-chip class="status-chip" [class]="'status-' + node.status">
                      {{ getStatusLabel(node.status) }}
                    </mat-chip>
                  </div>
                  
                  <div class="node-stats" *ngIf="node.type === 'module'">
                    <span class="stat-item">{{ getModuleScreenCount(node) }} pantallas</span>
                    <span class="stat-item">{{ getModuleProgress(node) }}% completado</span>
                  </div>
                </div>
              </mat-tree-node>
            </mat-tree>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .modules-container {
      padding: 20px;
      height: 100%;
    }
    
    .modules-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
    }
    
    .modules-header h1 {
      margin: 0;
      color: #333;
      font-weight: 300;
    }
    
    .header-actions {
      display: flex;
      gap: 10px;
    }
    
    .modules-content {
      height: calc(100vh - 140px);
    }
    
    .modules-tree-card {
      height: 100%;
    }
    
    .tree-node {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 8px 0;
      border-bottom: 1px solid #f0f0f0;
    }
    
    .node-content {
      display: flex;
      align-items: center;
      gap: 8px;
      flex: 1;
    }
    
    .node-icon {
      font-size: 20px;
    }
    
    .node-icon.node-type-module {
      color: #2196F3;
    }
    
    .node-icon.node-type-screen {
      color: #4CAF50;
    }
    
    .node-name {
      font-weight: 500;
    }
    
    .status-chip {
      font-size: 11px;
      height: 24px;
      border-radius: 12px;
    }
    
    .status-chip.status-pending {
      background-color: #f5f5f5;
      color: #666;
    }
    
    .status-chip.status-analyzing {
      background-color: #FFF3E0;
      color: #F57C00;
    }
    
    .status-chip.status-analyzed {
      background-color: #E8F5E8;
      color: #2E7D32;
    }
    
    .status-chip.status-generated {
      background-color: #E3F2FD;
      color: #1976D2;
    }
    
    .status-chip.status-error {
      background-color: #FFEBEE;
      color: #C62828;
    }
    
    .node-actions {
      display: flex;
      gap: 4px;
    }
    
    .node-stats {
      display: flex;
      gap: 15px;
      font-size: 12px;
      color: #666;
    }
    
    .stat-item {
      background-color: #f0f0f0;
      padding: 2px 8px;
      border-radius: 10px;
    }
    
    @media (max-width: 768px) {
      .modules-header {
        flex-direction: column;
        gap: 10px;
        align-items: flex-start;
      }
      
      .header-actions {
        width: 100%;
      }
      
      .node-actions {
        flex-direction: column;
      }
    }
  `]
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
      estimatedHours: node.estimatedHours
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

  constructor(private dialog: MatDialog) {
    this.dataSource.data = this.TREE_DATA;
  }

  ngOnInit() {
    // Expandir todos los nodos por defecto
    this.treeControl.expandAll();
  }

  hasChild = (_: number, node: FlatNode) => node.expandable;

  getStatusLabel(status: string): string {
    const labels = {
      'pending': 'Pendiente',
      'analyzing': 'Analizando',
      'analyzed': 'Analizada',
      'generated': 'Generada',
      'error': 'Error'
    };
    return labels[status as keyof typeof labels] || status;
  }

  getTreeStats(): string {
    const totalScreens = this.countScreens(this.TREE_DATA);
    const analyzedScreens = this.countScreensByStatus(this.TREE_DATA, 'analyzed');
    const generatedScreens = this.countScreensByStatus(this.TREE_DATA, 'generated');
    
    return `${totalScreens} pantallas total • ${analyzedScreens} analizadas • ${generatedScreens} generadas`;
  }

  countScreens(nodes: ModuleNode[]): number {
    return nodes.reduce((count, node) => {
      if (node.type === 'screen') {
        return count + 1;
      }
      return count + (node.children ? this.countScreens(node.children) : 0);
    }, 0);
  }

  countScreensByStatus(nodes: ModuleNode[], status: string): number {
    return nodes.reduce((count, node) => {
      if (node.type === 'screen' && node.status === status) {
        return count + 1;
      }
      return count + (node.children ? this.countScreensByStatus(node.children, status) : 0);
    }, 0);
  }

  getModuleScreenCount(node: FlatNode): number {
    // Implementar lógica para contar pantallas en un módulo
    return 2; // Mock
  }

  getModuleProgress(node: FlatNode): number {
    // Implementar lógica para calcular progreso
    return 50; // Mock
  }

  refreshModules() {
    console.log('Refreshing modules...');
    // Implementar lógica de actualización
  }

  vectorizeCode() {
    console.log('Vectorizing code...');
    // Implementar lógica de vectorización
  }

  analyzeScreen(node: FlatNode) {
    console.log('Analyzing screen:', node.name);
    // Implementar lógica de análisis
    // Actualizar estado del nodo
  }

  viewAnalysis(node: FlatNode) {
    console.log('Viewing analysis for:', node.name);
    this.openAnalysisModal(node);
  }

  generateCode(node: FlatNode) {
    console.log('Generating code for:', node.name);
    // Implementar lógica de generación
  }

  assignDeveloper(node: FlatNode) {
    console.log('Assigning developer to:', node.name);
    // Implementar lógica de asignación
  }

  viewCode(node: FlatNode) {
    console.log('Viewing SCR code for:', node.name);
    // Implementar modal para mostrar código SCR
  }

  exportAnalysis(node: FlatNode) {
    console.log('Exporting analysis for:', node.name);
    // Implementar lógica de exportación
  }

  openAnalysisModal(node: FlatNode) {
    const dialogRef = this.dialog.open(AnalysisModalComponent, {
      width: '90vw',
      maxWidth: '1200px',
      height: '80vh',
      data: {
        screenName: node.name,
        screenId: node.id,
        analysisData: this.getMockAnalysisData()
      }
    });

    dialogRef.afterClosed().subscribe(result => {
      console.log('Analysis modal closed:', result);
    });
  }

  getMockAnalysisData(): AnalysisData {
    return {
      frontend: {
        fields: [
          { name: 'numeroFactura', type: 'text', required: true, validation: 'numeric' },
          { name: 'fechaFactura', type: 'date', required: true },
          { name: 'clienteId', type: 'select', required: true, datasource: 'clientes' }
        ],
        validations: [
          { field: 'numeroFactura', rule: 'unique', message: 'El número de factura debe ser único' },
          { field: 'fechaFactura', rule: 'dateRange', message: 'La fecha debe estar en el rango permitido' }
        ],
        dependencies: ['ClienteService', 'FacturacionService', 'ValidationService'],
        buttons: [
          { name: 'Guardar', action: 'save', validation: true },
          { name: 'Cancelar', action: 'cancel' },
          { name: 'Imprimir', action: 'print', condition: 'saved' }
        ],
        presentationLogic: 'La pantalla maneja la creación y edición de facturas con validaciones en tiempo real',
        uiComponents: [
          { type: 'FormGroup', name: 'facturaForm' },
          { type: 'DataTable', name: 'detalleFactura' },
          { type: 'Modal', name: 'clienteSelector' }
        ]
      },
      backend: {
        businessLogic: 'Gestión completa del ciclo de vida de facturas incluyendo validaciones de negocio',
        sqlQueries: [
          { type: 'INSERT', table: 'facturas', description: 'Inserción de nueva factura' },
          { type: 'SELECT', table: 'clientes', description: 'Obtención de datos del cliente' },
          { type: 'UPDATE', table: 'inventario', description: 'Actualización de stock' }
        ],
        validations: [
          { type: 'business', rule: 'clienteActivo', message: 'El cliente debe estar activo' },
          { type: 'business', rule: 'stockDisponible', message: 'Verificar stock disponible' }
        ],
        externalCalls: [
          { service: 'SunatService', method: 'validarRuc', async: true },
          { service: 'EmailService', method: 'enviarFactura', async: true }
        ],
        dataTransformations: [
          { from: 'NSDK_FACTURA', to: 'FacturaDTO', description: 'Transformación de entidad legacy' }
        ],
        dependencies: ['FacturaRepository', 'ClienteService', 'InventarioService', 'SunatService']
      },
      api: {
        endpoints: [
          { method: 'POST', path: '/api/facturas', description: 'Crear nueva factura' },
          { method: 'GET', path: '/api/facturas/{id}', description: 'Obtener factura por ID' },
          { method: 'PUT', path: '/api/facturas/{id}', description: 'Actualizar factura' }
        ],
        openapiSpec: `
openapi: 3.0.0
info:
  title: Facturación API
  version: 1.0.0
paths:
  /api/facturas:
    post:
      summary: Crear nueva factura
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/FacturaCreate'
      responses:
        '201':
          description: Factura creada exitosamente
components:
  schemas:
    FacturaCreate:
      type: object
      properties:
        numeroFactura:
          type: string
        fechaFactura:
          type: string
          format: date
        clienteId:
          type: integer
        `,
        securityRequirements: [
          { type: 'JWT', scope: 'facturacion:write' },
          { type: 'RBAC', roles: ['FACTURADOR', 'ADMIN'] }
        ],
        dataModels: [
          { name: 'FacturaDTO', fields: ['id', 'numeroFactura', 'fechaFactura', 'clienteId', 'total'] },
          { name: 'DetalleFacturaDTO', fields: ['id', 'facturaId', 'productoId', 'cantidad', 'precio'] }
        ],
        errorHandling: [
          { code: 'FACT001', message: 'Número de factura duplicado' },
          { code: 'FACT002', message: 'Cliente no encontrado' },
          { code: 'FACT003', message: 'Stock insuficiente' }
        ]
      }
    };
  }
}

@Component({
  selector: 'app-analysis-modal',
  standalone: true,
  imports: [
    CommonModule,
    MatDialogModule,
    MatTabsModule,
    MatButtonModule,
    MatIconModule,
    MatCardModule,
    MatChipsModule
  ],
  template: `
    <div class="analysis-modal">
      <div mat-dialog-title class="modal-header">
        <h2>Análisis de Pantalla: {{ data.screenName }}</h2>
        <button mat-icon-button mat-dialog-close>
          <mat-icon>close</mat-icon>
        </button>
      </div>
      
      <div mat-dialog-content class="modal-content">
        <mat-tab-group>
          <mat-tab label="Frontend">
            <div class="tab-content">
              <div class="analysis-section">
                <h3>Campos</h3>
                <div class="fields-grid">
                  <mat-card *ngFor="let field of data.analysisData.frontend.fields" class="field-card">
                    <mat-card-content>
                      <div class="field-header">
                        <strong>{{ field.name }}</strong>
                        <mat-chip [selected]="field.required" color="primary">
                          {{ field.type }}
                        </mat-chip>
                      </div>
                      <p *ngIf="field.validation">Validación: {{ field.validation }}</p>
                      <p *ngIf="field.datasource">Origen: {{ field.datasource }}</p>
                    </mat-card-content>
                  </mat-card>
                </div>
              </div>
              
              <div class="analysis-section">
                <h3>Validaciones</h3>
                <div class="validations-list">
                  <mat-card *ngFor="let validation of data.analysisData.frontend.validations" class="validation-card">
                    <mat-card-content>
                      <div class="validation-info">
                        <strong>{{ validation.field }}</strong>
                        <mat-chip>{{ validation.rule }}</mat-chip>
                      </div>
                      <p>{{ validation.message }}</p>
                    </mat-card-content>
                  </mat-card>
                </div>
              </div>
              
              <div class="analysis-section">
                <h3>Dependencias</h3>
                <div class="dependencies-chips">
                  <mat-chip *ngFor="let dep of data.analysisData.frontend.dependencies" color="accent">
                    {{ dep }}
                  </mat-chip>
                </div>
              </div>
            </div>
          </mat-tab>
          
          <mat-tab label="Backend">
            <div class="tab-content">
              <div class="analysis-section">
                <h3>Lógica de Negocio</h3>
                <mat-card>
                  <mat-card-content>
                    <p>{{ data.analysisData.backend.businessLogic }}</p>
                  </mat-card-content>
                </mat-card>
              </div>
              
              <div class="analysis-section">
                <h3>Consultas SQL</h3>
                <div class="sql-queries">
                  <mat-card *ngFor="let query of data.analysisData.backend.sqlQueries" class="sql-card">
                    <mat-card-content>
                      <div class="sql-header">
                        <mat-chip [color]="getSqlTypeColor(query.type)">{{ query.type }}</mat-chip>
                        <strong>{{ query.table }}</strong>
                      </div>
                      <p>{{ query.description }}</p>
                    </mat-card-content>
                  </mat-card>
                </div>
              </div>
              
              <div class="analysis-section">
                <h3>Llamadas Externas</h3>
                <div class="external-calls">
                  <mat-card *ngFor="let call of data.analysisData.backend.externalCalls" class="call-card">
                    <mat-card-content>
                      <div class="call-header">
                        <strong>{{ call.service }}</strong>
                        <mat-chip [selected]="call.async" color="warn">
                          {{ call.async ? 'Async' : 'Sync' }}
                        </mat-chip>
                      </div>
                      <p>{{ call.method }}</p>
                    </mat-card-content>
                  </mat-card>
                </div>
              </div>
            </div>
          </mat-tab>
          
          <mat-tab label="API">
            <div class="tab-content">
              <div class="analysis-section">
                <h3>Endpoints</h3>
                <div class="endpoints-list">
                  <mat-card *ngFor="let endpoint of data.analysisData.api.endpoints" class="endpoint-card">
                    <mat-card-content>
                      <div class="endpoint-header">
                        <mat-chip [color]="getMethodColor(endpoint.method)">{{ endpoint.method }}</mat-chip>
                        <code>{{ endpoint.path }}</code>
                      </div>
                      <p>{{ endpoint.description }}</p>
                    </mat-card-content>
                  </mat-card>
                </div>
              </div>
              
              <div class="analysis-section">
                <h3>Especificación OpenAPI</h3>
                <mat-card>
                  <mat-card-content>
                    <pre><code>{{ data.analysisData.api.openapiSpec }}</code></pre>
                  </mat-card-content>
                </mat-card>
              </div>
              
              <div class="analysis-section">
                <h3>Modelos de Datos</h3>
                <div class="data-models">
                  <mat-card *ngFor="let model of data.analysisData.api.dataModels" class="model-card">
                    <mat-card-content>
                      <h4>{{ model.name }}</h4>
                      <div class="model-fields">
                        <mat-chip *ngFor="let field of model.fields">{{ field }}</mat-chip>
                      </div>
                    </mat-card-content>
                  </mat-card>
                </div>
              </div>
            </div>
          </mat-tab>
        </mat-tab-group>
      </div>
      
      <div mat-dialog-actions class="modal-actions">
        <button mat-button mat-dialog-close>Cerrar</button>
        <button mat-raised-button color="primary" (click)="generateCode()">
          <mat-icon>code</mat-icon>
          Generar Código
        </button>
        <button mat-raised-button color="accent" (click)="exportAnalysis()">
          <mat-icon>download</mat-icon>
          Exportar
        </button>
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
      padding: 0 24px;
    }
    
    .modal-content {
      flex: 1;
      overflow: auto;
    }
    
    .tab-content {
      padding: 20px;
    }
    
    .analysis-section {
      margin-bottom: 30px;
    }
    
    .analysis-section h3 {
      margin-bottom: 15px;
      color: #333;
    }
    
    .fields-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 15px;
    }
    
    .field-card {
      border-left: 4px solid #2196F3;
    }
    
    .field-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    
    .validations-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .validation-card {
      border-left: 4px solid #FF9800;
    }
    
    .validation-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    
    .dependencies-chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    
    .sql-queries {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .sql-card {
      border-left: 4px solid #4CAF50;
    }
    
    .sql-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
    }
    
    .external-calls {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .call-card {
      border-left: 4px solid #9C27B0;
    }
    
    .call-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 10px;
    }
    
    .endpoints-list {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .endpoint-card {
      border-left: 4px solid #FF5722;
    }
    
    .endpoint-header {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 10px;
    }
    
    .data-models {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 15px;
    }
    
    .model-card {
      border-left: 4px solid #607D8B;
    }
    
    .model-fields {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
    }
    
    .modal-actions {
      padding: 16px 24px;
      display: flex;
      justify-content: flex-end;
      gap: 10px;
    }
    
    pre {
      background-color: #f5f5f5;
      padding: 15px;
      border-radius: 4px;
      overflow-x: auto;
    }
    
    code {
      font-family: 'Courier New', monospace;
      background-color: #f0f0f0;
      padding: 2px 4px;
      border-radius: 3px;
    }
  `]
})
export class AnalysisModalComponent {
  constructor(
    public dialogRef: MatDialogRef<AnalysisModalComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {}

  getSqlTypeColor(type: string): string {
    const colors = {
      'SELECT': 'primary',
      'INSERT': 'accent',
      'UPDATE': 'warn',
      'DELETE': 'warn'
    };
    return colors[type as keyof typeof colors] || 'primary';
  }

  getMethodColor(method: string): string {
    const colors = {
      'GET': 'primary',
      'POST': 'accent',
      'PUT': 'warn',
      'DELETE': 'warn'
    };
    return colors[method as keyof typeof colors] || 'primary';
  }

  generateCode() {
    console.log('Generating code from analysis...');
    // Implementar lógica de generación de código
    this.dialogRef.close('generate');
  }

  exportAnalysis() {
    console.log('Exporting analysis...');
    // Implementar lógica de exportación
    this.dialogRef.close('export');
  }
}

// Necesitamos estas importaciones para el modal
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Inject } from '@angular/core';