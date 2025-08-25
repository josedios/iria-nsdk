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
  templateUrl: './knowledge.component.html',
  styleUrls: ['./knowledge.component.scss']
})
export class KnowledgeComponent implements OnInit {
  // Estados
  isVectorizing = false;
  isSearching = false;
  isLoadingDocuments = false;

  // Datos de estadísticas
  stats: LocalVectorizationStats = {
    totalDocuments: 0,
    sourceDocuments: 0,
    targetDocuments: 0,
    documentationDocuments: 0,
    lastUpdated: 'Nunca',
    collectionSize: '0 archivos'
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
    // Primero cargar estadísticas, luego documentos basados en estadísticas reales
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

        // Después de cargar estadísticas, cargar documentos
        this.loadDocuments();
      },
      error: (error) => {
        console.error('Error cargando estadísticas:', error);
        // Mantener estadísticas por defecto y cargar documentos
        this.loadDocuments();
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
            // Refrescar todos los datos después de la vectorización
            this.refreshAllData();
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
    this.isLoadingDocuments = true;
    console.log('Cargando documentos del backend...');

    // TODO: Implementar endpoint real para obtener documentos
    // Por ahora, usar estadísticas para generar documentos simulados
    // pero en el futuro esto debería ser una llamada real al backend

    if (this.hasVectorizationData()) {
      // Si hay datos de vectorización, generar documentos basados en estadísticas reales
      setTimeout(() => {
        this.documents = this.generateSimulatedDocuments();
        this.isLoadingDocuments = false;
        console.log(`Documentos generados basados en estadísticas: ${this.documents.length}`);
      }, 500);
    } else {
      // Si no hay datos, mostrar documentos de ejemplo
      setTimeout(() => {
        this.documents = this.generateExampleDocuments();
        this.isLoadingDocuments = false;
        console.log('Documentos de ejemplo generados:', this.documents.length);
      }, 500);
    }
  }

  private generateSimulatedDocuments(): DocumentInfo[] {
    const documents: DocumentInfo[] = [];
    console.log('Generando documentos simulados con estadísticas:', this.stats);

    // Generar documentos NSDK basados en las estadísticas
    if (this.stats.sourceDocuments > 0) {
      const numDocs = Math.min(this.stats.sourceDocuments, 20); // Mostrar hasta 20 documentos
      console.log(`Generando ${numDocs} documentos NSDK`);

      for (let i = 1; i <= numDocs; i++) {
        documents.push({
          id: `nsdk_${i}`,
          name: `NSDK_File_${i}.SCR`,
          type: 'nsdk_source' as const,
          size: `${Math.floor(Math.random() * 10 + 1)}.${Math.floor(Math.random() * 9)} KB`,
          lastModified: new Date().toLocaleString(),
          status: 'indexed' as const
        });
      }
    }

    // Generar documentos de código moderno
    if (this.stats.targetDocuments > 0) {
      for (let i = 1; i <= Math.min(this.stats.targetDocuments, 5); i++) {
        documents.push({
          id: `target_${i}`,
          name: `Component_${i}.ts`,
          type: 'target_code' as const,
          size: `${Math.floor(Math.random() * 20 + 5)}.${Math.floor(Math.random() * 9)} KB`,
          lastModified: new Date().toLocaleString(),
          status: 'indexed' as const
        });
      }
    }

    // Generar documentos de documentación
    if (this.stats.documentationDocuments > 0) {
      for (let i = 1; i <= Math.min(this.stats.documentationDocuments, 3); i++) {
        documents.push({
          id: `doc_${i}`,
          name: `Documentation_${i}.pdf`,
          type: 'documentation' as const,
          size: `${Math.floor(Math.random() * 5 + 1)}.${Math.floor(Math.random() * 9)} MB`,
          lastModified: new Date().toLocaleString(),
          status: 'indexed' as const
        });
      }
    }

    return documents;
  }

  private generateExampleDocuments(): DocumentInfo[] {
    // Documentos de ejemplo para mostrar cuando no hay vectorización
    return [
      {
        id: '1',
        name: 'FACT001.SCR',
        type: 'nsdk_source' as const,
        size: '2.4 KB',
        lastModified: '2024-01-15 10:30',
        status: 'pending' as const
      },
      {
        id: '2',
        name: 'InvoiceComponent.ts',
        type: 'target_code' as const,
        size: '8.7 KB',
        lastModified: '2024-01-15 09:15',
        status: 'indexed' as const
      },
      {
        id: '3',
        name: 'business-rules.pdf',
        type: 'documentation' as const,
        size: '1.2 MB',
        lastModified: '2024-01-14 16:45',
        status: 'pending' as const
      }
    ];
  }

  private refreshAllData() {
    // Refresca todos los datos después de una vectorización
    // Primero cargar estadísticas, luego documentos cuando las estadísticas estén listas
    this.knowledgeService.getVectorizationStats().subscribe({
      next: (stats: VectorizationStats) => {
        console.log('Estadísticas actualizadas después de vectorización:', stats);
        // Mapear propiedades del backend a la interfaz local
        this.stats.totalDocuments = stats.total_files || 0;
        this.stats.sourceDocuments = stats.vectorized_files || 0;
        this.stats.targetDocuments = 0; // Por ahora
        this.stats.documentationDocuments = 0; // Por ahora
        this.stats.lastUpdated = stats.last_vectorization || 'Nunca';
        this.stats.collectionSize = `${stats.total_files || 0} archivos`;

        // Ahora cargar documentos con las estadísticas actualizadas
        this.loadDocuments();
        console.log('Documentos actualizados después de vectorización');
      },
      error: (error) => {
        console.error('Error cargando estadísticas después de vectorización:', error);
        // Intentar cargar documentos con estadísticas existentes
        this.loadDocuments();
      }
    });
  }

  // TODO: Implementar cuando el backend tenga endpoint para documentos
  private loadRealDocumentsFromBackend() {
    // Este método debería:
    // 1. Llamar a this.knowledgeService.getDocuments()
    // 2. Mapear la respuesta a DocumentInfo[]
    // 3. Actualizar this.documents
    // 4. Mantener persistencia real entre sesiones

    console.log('Método para cargar documentos reales del backend (a implementar)');

    // Ejemplo de implementación futura:
    /*
    this.knowledgeService.getDocuments().subscribe({
      next: (response) => {
        this.documents = response.documents.map(doc => ({
          id: doc.id,
          name: doc.name,
          type: doc.type,
          size: doc.size,
          lastModified: doc.last_modified,
          status: doc.status
        }));
        this.isLoadingDocuments = false;
      },
      error: (error) => {
        console.error('Error cargando documentos del backend:', error);
        this.isLoadingDocuments = false;
        // Fallback a documentos simulados
        this.documents = this.generateSimulatedDocuments();
      }
    });
    */
  }

  // Métodos auxiliares para el template
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

  refreshDocuments() {
    console.log('Actualizando documentos manualmente...');
    // Refrescar estadísticas primero, luego documentos
    this.loadVectorizationStats();
  }

  hasVectorizationData(): boolean {
    return this.stats.totalDocuments > 0 || this.stats.sourceDocuments > 0;
  }

  getVectorizationStatus(): string {
    if (this.stats.totalDocuments === 0) {
      return 'No hay datos de vectorización';
    } else if (this.stats.sourceDocuments > 0) {
      return `${this.stats.sourceDocuments} archivos vectorizados de ${this.stats.totalDocuments} total`;
    } else {
      return `${this.stats.totalDocuments} archivos pendientes de vectorización`;
    }
  }
}