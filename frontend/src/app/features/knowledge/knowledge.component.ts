import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { KnowledgeService, SearchCodeRequest, VectorizationBatch, VectorizationStats, VectorizeRepositoryRequest } from './knowledge.service';
import { VectorizeRepoDialogComponent, VectorizeRepoDialogData } from './vectorize-repo-dialog.component';

// Interfaces locales para el componente
interface LocalVectorizationStats {
  totalDocuments: number;
  sourceDocuments: number;
  targetDocuments: number;
  documentationDocuments: number;
  lastUpdated: string;
  collectionSize: string;
}

interface DocumentInfo {
  id: string;
  name: string;
  type: 'nsdk_source' | 'target_code' | 'documentation';
  size: string;
  lastModified: string;
  status: 'indexed' | 'pending' | 'error';
  similarity?: number;
}

// Interfaz local para resultados de búsqueda (compatible con el template)
interface LocalSearchResult {
  id: string;
  content: string;
  metadata: {
    source: string;
    file_path: string;
    file_type: string;
  };
  similarity: number;
}

@Component({
  selector: 'app-knowledge',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatProgressBarModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatSnackBarModule,
    MatDialogModule,
    MatProgressSpinnerModule
  ],
  template: `
    <div class="knowledge-container">
      <div class="knowledge-header">
        <h1>Gestión de Conocimiento</h1>
        <div class="header-actions">
          <button mat-raised-button color="primary" (click)="vectorizeRepositories()" [disabled]="isVectorizing">
            <mat-icon>upload</mat-icon>
            {{ isVectorizing ? 'Vectorizando...' : 'Vectorizar Repositorios' }}
          </button>
          <button mat-raised-button color="accent" (click)="openDocumentUpload()">
            <mat-icon>library_add</mat-icon>
            Subir Documentación
          </button>
        </div>
      </div>

      <mat-tab-group class="knowledge-tabs">
        <!-- Estadísticas de Vectorización -->
        <mat-tab label="Estadísticas">
          <div class="tab-content">
            <div class="stats-grid">
              <mat-card class="stat-card">
                <mat-card-content>
                  <div class="stat-content">
                    <mat-icon class="stat-icon documents">description</mat-icon>
                    <div class="stat-info">
                      <h3>{{ stats.totalDocuments | number }}</h3>
                      <p>Documentos Totales</p>
                    </div>
                  </div>
                </mat-card-content>
              </mat-card>

              <mat-card class="stat-card">
                <mat-card-content>
                  <div class="stat-content">
                    <mat-icon class="stat-icon source">code</mat-icon>
                    <div class="stat-info">
                      <h3>{{ stats.sourceDocuments | number }}</h3>
                      <p>Código NSDK</p>
                    </div>
                  </div>
                </mat-card-content>
              </mat-card>

              <mat-card class="stat-card">
                <mat-card-content>
                  <div class="stat-content">
                    <mat-icon class="stat-icon target">web</mat-icon>
                    <div class="stat-info">
                      <h3>{{ stats.targetDocuments | number }}</h3>
                      <p>Código Moderno</p>
                    </div>
                  </div>
                </mat-card-content>
              </mat-card>

              <mat-card class="stat-card">
                <mat-card-content>
                  <div class="stat-content">
                    <mat-icon class="stat-icon docs">library_books</mat-icon>
                    <div class="stat-info">
                      <h3>{{ stats.documentationDocuments | number }}</h3>
                      <p>Documentación</p>
                    </div>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>

            <!-- Progreso de Vectorización -->
            <mat-card class="progress-card" *ngIf="isVectorizing">
              <mat-card-header>
                <mat-card-title>Progreso de Vectorización</mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <div class="progress-info">
                  <p>{{ vectorizationStatus }}</p>
                  <mat-progress-bar mode="determinate" [value]="vectorizationProgress"></mat-progress-bar>
                  <div class="progress-details">
                    <span>{{ vectorizationProgress }}% completado</span>
                    <span>{{ processedFiles }}/{{ totalFiles }} archivos</span>
                  </div>
                </div>
              </mat-card-content>
            </mat-card>

            <!-- Información del Vector Store -->
            <mat-card class="info-card">
              <mat-card-header>
                <mat-card-title>
                  <mat-icon>storage</mat-icon>
                  Información del Vector Store
                </mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <div class="info-grid">
                  <div class="info-item">
                    <span class="info-label">Tamaño de Colección:</span>
                    <span class="info-value">{{ stats.collectionSize }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Última Actualización:</span>
                    <span class="info-value">{{ stats.lastUpdated }}</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Modelo de Embeddings:</span>
                    <span class="info-value">text-embedding-3-small</span>
                  </div>
                  <div class="info-item">
                    <span class="info-label">Dimensiones:</span>
                    <span class="info-value">1536</span>
                  </div>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </mat-tab>

        <!-- Búsqueda Semántica -->
        <mat-tab label="Búsqueda">
          <div class="tab-content">
            <mat-card class="search-card">
              <mat-card-header>
                <mat-card-title>
                  <mat-icon>search</mat-icon>
                  Búsqueda Semántica de Código
                </mat-card-title>
                <mat-card-subtitle>Encuentra código similar usando IA</mat-card-subtitle>
              </mat-card-header>
              <mat-card-content>
                <div class="search-form">
                  <mat-form-field appearance="outline" class="search-field">
                    <mat-label>Buscar código o funcionalidad</mat-label>
                    <textarea matInput 
                              [(ngModel)]="searchQuery" 
                              placeholder="Ejemplo: función que calcula impuestos de factura"
                              rows="3">
                    </textarea>
                    <mat-icon matSuffix>search</mat-icon>
                  </mat-form-field>
                  
                  <div class="search-options">
                    <mat-form-field appearance="outline">
                      <mat-label>Tipo de Código</mat-label>
                      <mat-select [(ngModel)]="searchType">
                        <mat-option value="all">Todos</mat-option>
                        <mat-option value="nsdk_source">Código NSDK</mat-option>
                        <mat-option value="target_code">Código Moderno</mat-option>
                        <mat-option value="documentation">Documentación</mat-option>
                      </mat-select>
                    </mat-form-field>
                    
                    <button mat-raised-button color="primary" (click)="performSearch()" [disabled]="!searchQuery || isSearching">
                      <mat-icon>search</mat-icon>
                      {{ isSearching ? 'Buscando...' : 'Buscar' }}
                    </button>
                  </div>
                </div>
              </mat-card-content>
            </mat-card>

            <!-- Resultados de Búsqueda -->
            <mat-card class="results-card" *ngIf="searchResults.length > 0">
              <mat-card-header>
                <mat-card-title>
                  <mat-icon>search</mat-icon>
                  Resultados de Búsqueda ({{ searchResults.length }})
                </mat-card-title>
              </mat-card-header>
              <mat-card-content>
                <div class="search-results">
                  <div class="result-item" *ngFor="let result of searchResults; trackBy: trackByResultId">
                    <div class="result-header">
                      <div class="result-info">
                        <h4>{{ getFileName(result.metadata.file_path) }}</h4>
                        <div class="result-meta">
                          <mat-chip [class]="'type-chip ' + result.metadata.source">
                            {{ getSourceLabel(result.metadata.source) }}
                          </mat-chip>
                          <span class="similarity">{{ (result.similarity * 100) | number:'1.1-1' }}% similar</span>
                        </div>
                      </div>
                      <button mat-icon-button (click)="viewResultDetails(result)">
                        <mat-icon>visibility</mat-icon>
                      </button>
                    </div>
                    
                    <div class="result-content">
                      <pre><code>{{ result.content | slice:0:300 }}{{ result.content.length > 300 ? '...' : '' }}</code></pre>
                    </div>
                    
                    <div class="result-actions">
                      <button mat-button color="primary" (click)="copyToClipboard(result.content)">
                        <mat-icon>content_copy</mat-icon>
                        Copiar
                      </button>
                      <button mat-button (click)="findSimilar(result)">
                        <mat-icon>find_in_page</mat-icon>
                        Buscar Similar
                      </button>
                    </div>
                  </div>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </mat-tab>

        <!-- Gestión de Documentos -->
        <mat-tab label="Documentos">
          <div class="tab-content">
            <mat-card class="documents-card">
              <mat-card-header>
                <mat-card-title>
                  <mat-icon>folder</mat-icon>
                  Documentos Indexados
                </mat-card-title>
                <mat-card-subtitle>Gestión de archivos en el vector store</mat-card-subtitle>
              </mat-card-header>
              <mat-card-content>
                <div class="table-container">
                  <table mat-table [dataSource]="documents" class="documents-table">
                    <!-- Nombre Column -->
                    <ng-container matColumnDef="name">
                      <th mat-header-cell *matHeaderCellDef>Nombre</th>
                      <td mat-cell *matCellDef="let doc">
                        <div class="doc-name">
                          <mat-icon [class]="'doc-icon ' + doc.type">
                            {{ getDocumentIcon(doc.type) }}
                          </mat-icon>
                          {{ doc.name }}
                        </div>
                      </td>
                    </ng-container>

                    <!-- Tipo Column -->
                    <ng-container matColumnDef="type">
                      <th mat-header-cell *matHeaderCellDef>Tipo</th>
                      <td mat-cell *matCellDef="let doc">
                        <mat-chip [class]="'type-chip ' + doc.type">
                          {{ getTypeLabel(doc.type) }}
                        </mat-chip>
                      </td>
                    </ng-container>

                    <!-- Tamaño Column -->
                    <ng-container matColumnDef="size">
                      <th mat-header-cell *matHeaderCellDef>Tamaño</th>
                      <td mat-cell *matCellDef="let doc">{{ doc.size }}</td>
                    </ng-container>

                    <!-- Estado Column -->
                    <ng-container matColumnDef="status">
                      <th mat-header-cell *matHeaderCellDef>Estado</th>
                      <td mat-cell *matCellDef="let doc">
                        <mat-chip [class]="'status-chip ' + doc.status">
                          {{ getStatusLabel(doc.status) }}
                        </mat-chip>
                      </td>
                    </ng-container>

                    <!-- Última Modificación Column -->
                    <ng-container matColumnDef="lastModified">
                      <th mat-header-cell *matHeaderCellDef>Última Modificación</th>
                      <td mat-cell *matCellDef="let doc">{{ doc.lastModified }}</td>
                    </ng-container>

                    <!-- Acciones Column -->
                    <ng-container matColumnDef="actions">
                      <th mat-header-cell *matHeaderCellDef>Acciones</th>
                      <td mat-cell *matCellDef="let doc">
                        <button mat-icon-button (click)="reindexDocument(doc)">
                          <mat-icon>refresh</mat-icon>
                        </button>
                        <button mat-icon-button color="warn" (click)="deleteDocument(doc)">
                          <mat-icon>delete</mat-icon>
                        </button>
                      </td>
                    </ng-container>

                    <tr mat-header-row *matHeaderRowDef="displayedColumns"></tr>
                    <tr mat-row *matRowDef="let row; columns: displayedColumns;"></tr>
                  </table>
                </div>
              </mat-card-content>
            </mat-card>
          </div>
        </mat-tab>
      </mat-tab-group>
    </div>
  `,
  styles: [`
    .knowledge-container {
      padding: 20px;
    }
    
    .knowledge-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30px;
    }
    
    .knowledge-header h1 {
      margin: 0;
      color: #333;
      font-weight: 300;
    }
    
    .header-actions {
      display: flex;
      gap: 10px;
    }
    
    .knowledge-tabs {
      width: 100%;
    }
    
    .tab-content {
      padding: 20px 0;
    }
    
    .stats-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
      margin-bottom: 30px;
    }
    
    .stat-card {
      height: 120px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .stat-content {
      display: flex;
      align-items: center;
      gap: 15px;
    }
    
    .stat-icon {
      font-size: 36px;
      width: 36px;
      height: 36px;
    }
    
    .stat-icon.documents { color: #2196F3; }
    .stat-icon.source { color: #4CAF50; }
    .stat-icon.target { color: #FF9800; }
    .stat-icon.docs { color: #9C27B0; }
    
    .stat-info h3 {
      margin: 0;
      font-size: 24px;
      font-weight: 500;
    }
    
    .stat-info p {
      margin: 5px 0 0 0;
      color: #666;
      font-size: 14px;
    }
    
    .progress-card, .info-card, .search-card, .results-card, .documents-card {
      margin-bottom: 20px;
    }
    
    .progress-info {
      text-align: center;
    }
    
    .progress-details {
      display: flex;
      justify-content: space-between;
      margin-top: 10px;
      font-size: 12px;
      color: #666;
    }
    
    .info-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 15px;
    }
    
    .info-item {
      display: flex;
      flex-direction: column;
      padding: 10px;
      background-color: #f8f9fa;
      border-radius: 4px;
    }
    
    .info-label {
      font-size: 12px;
      color: #666;
      margin-bottom: 5px;
    }
    
    .info-value {
      font-weight: 500;
    }
    
    .search-form {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    
    .search-field {
      width: 100%;
    }
    
    .search-options {
      display: flex;
      gap: 15px;
      align-items: center;
    }
    
    .search-results {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    
    .result-item {
      border: 1px solid #e0e0e0;
      border-radius: 8px;
      overflow: hidden;
    }
    
    .result-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 15px 20px;
      background-color: #f8f9fa;
      border-bottom: 1px solid #e0e0e0;
    }
    
    .result-info h4 {
      margin: 0 0 5px 0;
      font-size: 16px;
    }
    
    .result-meta {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    .type-chip {
      font-size: 11px;
      height: 20px;
    }
    
    .type-chip.nsdk_source { background-color: #E8F5E8; color: #2E7D32; }
    .type-chip.target_code { background-color: #FFF3E0; color: #F57C00; }
    .type-chip.documentation { background-color: #E3F2FD; color: #1976D2; }
    
    .similarity {
      font-size: 12px;
      color: #666;
    }
    
    .result-content {
      padding: 20px;
    }
    
    .result-content pre {
      background-color: #f5f5f5;
      padding: 15px;
      border-radius: 4px;
      margin: 0;
      overflow-x: auto;
      font-size: 12px;
    }
    
    .result-actions {
      padding: 10px 20px;
      border-top: 1px solid #e0e0e0;
      display: flex;
      gap: 10px;
    }
    
    .table-container {
      max-height: 500px;
      overflow: auto;
    }
    
    .documents-table {
      width: 100%;
    }
    
    .doc-name {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    .doc-icon {
      font-size: 18px;
    }
    
    .doc-icon.nsdk_source { color: #4CAF50; }
    .doc-icon.target_code { color: #FF9800; }
    .doc-icon.documentation { color: #2196F3; }
    
    .status-chip.indexed { background-color: #E8F5E8; color: #2E7D32; }
    .status-chip.pending { background-color: #FFF3E0; color: #F57C00; }
    .status-chip.error { background-color: #FFEBEE; color: #C62828; }
    
    mat-card-header mat-card-title {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    @media (max-width: 768px) {
      .knowledge-header {
        flex-direction: column;
        gap: 15px;
        align-items: flex-start;
      }
      
      .header-actions {
        width: 100%;
      }
      
      .stats-grid {
        grid-template-columns: 1fr;
      }
      
      .search-options {
        flex-direction: column;
        align-items: stretch;
      }
    }
  `]
})
export class KnowledgeComponent implements OnInit {
  // Estados
  isVectorizing = false;
  isSearching = false;

  // Datos de estadísticas
  stats: LocalVectorizationStats = {
    totalDocuments: 1247,
    sourceDocuments: 823,
    targetDocuments: 312,
    documentationDocuments: 112,
    lastUpdated: '2024-01-15 14:30:00',
    collectionSize: '2.3 GB'
  };

  // Progreso de vectorización
  vectorizationStatus = '';
  vectorizationProgress = 0;
  processedFiles = 0;
  totalFiles = 0;

  // Búsqueda
  searchQuery = '';
  searchType = 'all';
  searchResults: LocalSearchResult[] = [];

  // Documentos
  documents: DocumentInfo[] = [];
  displayedColumns = ['name', 'type', 'size', 'status', 'lastModified', 'actions'];

  constructor(
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
    private knowledgeService: KnowledgeService
  ) { }

  ngOnInit() {
    this.loadDocuments();
    this.loadVectorizationStats();
  }

  vectorizeRepositories() {
    const dialogRef = this.dialog.open(VectorizeRepoDialogComponent, {
      width: '500px',
      data: {
        repo_url: '',
        branch: 'main',
        username: '',
        token: ''
      }
    });

    dialogRef.afterClosed().subscribe((result: VectorizeRepoDialogData) => {
      if (result && result.repo_url) {
        this.startVectorization(result);
      }
    });
  }

  private startVectorization(data: VectorizeRepoDialogData) {
    this.isVectorizing = true;
    this.vectorizationProgress = 0;
    this.processedFiles = 0;
    this.totalFiles = 0;
    this.vectorizationStatus = 'Iniciando vectorización...';

    const vectorizeRequest: VectorizeRepositoryRequest = {
      repo_url: data.repo_url,
      branch: data.branch,
      username: data.username || undefined,
      token: data.token || undefined
    };

    this.knowledgeService.vectorizeRepository(vectorizeRequest).subscribe({
      next: (response) => {
        console.log('Vectorización iniciada:', response);
        this.vectorizationStatus = `Vectorización iniciada. Lote: ${response.batch_id}`;

        // Monitorear progreso del lote
        if (response.batch_id) {
          this.monitorBatchProgress(response.batch_id);
        }
      },
      error: (error) => {
        console.error('Error en vectorización:', error);
        this.isVectorizing = false;
        this.vectorizationStatus = 'Error en vectorización';
        this.snackBar.open('Error al iniciar vectorización: ' + error.message, 'Cerrar', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }

  private loadVectorizationStats() {
    this.knowledgeService.getVectorizationStats().subscribe({
      next: (stats: VectorizationStats) => {
        console.log('Estadísticas de vectorización:', stats);
        // Mapear propiedades del backend a la interfaz local
        this.stats.totalDocuments = stats.total_files || 0;
        this.stats.sourceDocuments = stats.vectorized_files || 0;
        this.stats.targetDocuments = 0; // Por ahora
        this.stats.documentationDocuments = 0; // Por ahora
        this.stats.lastUpdated = stats.last_vectorization || 'Nunca';
        this.stats.collectionSize = `${stats.total_files || 0} archivos`;
      },
      error: (error) => {
        console.error('Error cargando estadísticas:', error);
        // Mantener estadísticas por defecto
      }
    });
  }

  private monitorBatchProgress(batchId: string) {
    const checkProgress = () => {
      this.knowledgeService.getBatchStatus(batchId).subscribe({
        next: (batch: VectorizationBatch) => {
          // Calcular progreso basado en archivos procesados
          this.vectorizationProgress = batch.total_files > 0 ?
            Math.round((batch.processed_files / batch.total_files) * 100) : 0;
          this.processedFiles = batch.processed_files || 0;
          this.totalFiles = batch.total_files || 0;

          if (batch.status === 'in_progress') {
            this.vectorizationStatus = 'Procesando archivos NSDK...';
            // Continuar monitoreando
            setTimeout(checkProgress, 2000);
          } else if (batch.status === 'completed') {
            this.isVectorizing = false;
            this.vectorizationStatus = 'Vectorización completada';
            this.snackBar.open('Vectorización completada exitosamente', 'Cerrar', {
              duration: 3000,
              panelClass: ['success-snackbar']
            });
            this.loadVectorizationStats();
          } else if (batch.status === 'failed') {
            this.isVectorizing = false;
            this.vectorizationStatus = 'Vectorización fallida';
            // Mensaje de error genérico ya que metadata no está disponible en VectorizationBatch
            this.snackBar.open('Vectorización fallida: Error en el proceso', 'Cerrar', {
              duration: 5000,
              panelClass: ['error-snackbar']
            });
          }
        },
        error: (error) => {
          console.error('Error obteniendo estado del lote:', error);
          this.vectorizationStatus = 'Error obteniendo progreso';
          setTimeout(checkProgress, 5000); // Reintentar
        }
      });
    };

    checkProgress();
  }

  performSearch() {
    if (!this.searchQuery) return;

    this.isSearching = true;
    this.searchResults = [];

    const searchRequest: SearchCodeRequest = {
      query: this.searchQuery,
      limit: 10
    };

    this.knowledgeService.searchSimilarCode(searchRequest).subscribe({
      next: (response) => {
        console.log('Resultados de búsqueda:', response);
        // Mapear resultados del backend a la interfaz local
        this.searchResults = response.results.map(result => ({
          id: result.id || '',
          content: result.metadata?.content || result.metadata?.file_path || 'Sin contenido',
          metadata: {
            source: result.metadata?.source || 'unknown',
            file_path: result.metadata?.file_path || '',
            file_type: result.metadata?.file_type || ''
          },
          similarity: result.score || 0
        })) as LocalSearchResult[];
        this.isSearching = false;

        if (this.searchResults.length === 0) {
          this.snackBar.open('No se encontraron resultados para tu búsqueda', 'Cerrar', {
            duration: 3000
          });
        }
      },
      error: (error) => {
        console.error('Error en búsqueda:', error);
        this.isSearching = false;
        this.snackBar.open('Error en búsqueda: ' + error.message, 'Cerrar', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }

  loadDocuments() {
    // Simular carga de documentos
    this.documents = [
      {
        id: '1',
        name: 'FACT001.SCR',
        type: 'nsdk_source',
        size: '2.4 KB',
        lastModified: '2024-01-15 10:30',
        status: 'indexed'
      },
      {
        id: '2',
        name: 'InvoiceComponent.ts',
        type: 'target_code',
        size: '8.7 KB',
        lastModified: '2024-01-15 09:15',
        status: 'indexed'
      },
      {
        id: '3',
        name: 'business-rules.pdf',
        type: 'documentation',
        size: '1.2 MB',
        lastModified: '2024-01-14 16:45',
        status: 'pending'
      }
    ];
  }

  // Métodos auxiliares
  trackByResultId(index: number, result: LocalSearchResult): string {
    return result.id;
  }

  getFileName(filePath: string): string {
    return filePath.split('/').pop() || filePath;
  }

  getSourceLabel(source: string): string {
    const labels = {
      'nsdk_source': 'NSDK Legacy',
      'target_code': 'Código Moderno',
      'documentation': 'Documentación'
    };
    return labels[source as keyof typeof labels] || source;
  }

  getDocumentIcon(type: string): string {
    const icons = {
      'nsdk_source': 'code',
      'target_code': 'web',
      'documentation': 'description'
    };
    return icons[type as keyof typeof icons] || 'description';
  }

  getTypeLabel(type: string): string {
    return this.getSourceLabel(type);
  }

  getStatusLabel(status: string): string {
    const labels = {
      'indexed': 'Indexado',
      'pending': 'Pendiente',
      'error': 'Error'
    };
    return labels[status as keyof typeof labels] || status;
  }

  // Acciones
  copyToClipboard(content: string) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(content).then(() => {
        this.snackBar.open('Código copiado al portapapeles', 'Cerrar', { duration: 2000 });
      }).catch(() => {
        this.snackBar.open('Error al copiar al portapapeles', 'Cerrar', { duration: 2000 });
      });
    } else {
      // Fallback para navegadores que no soportan clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = content;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      this.snackBar.open('Código copiado al portapapeles', 'Cerrar', { duration: 2000 });
    }
  }

  findSimilar(result: LocalSearchResult) {
    this.searchQuery = result.content.substring(0, 100) + '...';
    this.performSearch();
  }

  viewResultDetails(result: LocalSearchResult) {
    console.log('Viewing details for:', result);
    // Implementar modal con detalles completos
  }

  openDocumentUpload() {
    console.log('Opening document upload dialog');
    // Implementar modal de subida de documentos
  }

  reindexDocument(doc: DocumentInfo) {
    console.log('Reindexing document:', doc);
    // Implementar re-indexación
  }

  deleteDocument(doc: DocumentInfo) {
    console.log('Deleting document:', doc);
    // Implementar eliminación
  }
}