import { CommonModule } from '@angular/common';
import { Component, EventEmitter, OnInit, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSnackBar } from '@angular/material/snack-bar';
import { KnowledgeService } from './knowledge.service';

interface AvailableDocument {
    name: string;
    display_name: string;
    size_mb: number;
    path: string;
}

@Component({
    selector: 'app-document-selector',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatProgressSpinnerModule,
        MatListModule
    ],
    template: `
    <div class="selector-container">
      <div class="header">
        <h2>📚 Procesar Documentación NSDK</h2>
        <p class="subtitle">Selecciona los documentos PDF que deseas procesar para el análisis de IA</p>
      </div>
      
      <!-- Loading State -->
      <div *ngIf="isLoading" class="loading-container">
        <mat-spinner diameter="50"></mat-spinner>
        <p>Cargando documentos disponibles...</p>
      </div>
      
      <!-- Documents Grid -->
      <div *ngIf="availableDocuments.length > 0 && !isLoading" class="documents-section">
        <div class="section-header">
          <h3>📄 Documentos Disponibles</h3>
          <span class="count-badge">{{ availableDocuments.length }} documentos</span>
        </div>
        
        <div class="documents-grid">
          <mat-card 
            *ngFor="let doc of availableDocuments; trackBy: trackByDocumentName" 
            class="document-card"
            [class.processing]="processingDocuments.has(doc.name)"
            [class.processed]="isDocumentProcessed(doc.name)"
          >
            <div class="card-header">
              <div class="document-icon">
                <mat-icon>description</mat-icon>
              </div>
              <div class="document-info">
                <h4 class="document-title">{{ doc.display_name }}</h4>
                <p class="document-meta">
                  <span class="file-size">{{ doc.size_mb }} MB</span>
                  <span class="file-type">PDF</span>
                </p>
              </div>
            </div>
            
            <div class="card-content">
              <p class="document-description">
                {{ getDocumentDescription(doc.name) }}
              </p>
            </div>
            
            <div class="card-actions">
              <button 
                mat-raised-button 
                [color]="isDocumentProcessed(doc.name) ? 'accent' : 'primary'"
                (click)="processDocument(doc)"
                [disabled]="isProcessing || processingDocuments.has(doc.name)"
                class="process-button"
              >
                <mat-icon>{{ isDocumentProcessed(doc.name) ? 'check_circle' : 'cloud_upload' }}</mat-icon>
                {{ isDocumentProcessed(doc.name) ? 'Procesado' : 'Procesar' }}
              </button>
            </div>
            
            <!-- Processing Overlay -->
            <div *ngIf="processingDocuments.has(doc.name)" class="processing-overlay">
              <div class="processing-content">
                <mat-spinner diameter="40"></mat-spinner>
                <p>Procesando documento...</p>
                <small>Esto puede tomar unos minutos</small>
              </div>
            </div>
          </mat-card>
        </div>
      </div>
      
      <!-- No Documents State -->
      <div *ngIf="availableDocuments.length === 0 && !isLoading" class="no-documents">
        <div class="no-documents-content">
          <mat-icon class="empty-icon">folder_open</mat-icon>
          <h3>No se encontraron documentos</h3>
          <p>No hay documentos PDF en la carpeta NSDK-DOCS</p>
        </div>
      </div>
      
      <!-- Processed Documents Summary -->
      <div *ngIf="processedDocuments.length > 0" class="processed-summary">
        <div class="summary-header">
          <h3>✅ Documentos Procesados</h3>
          <span class="count-badge success">{{ processedDocuments.length }} completados</span>
        </div>
        <div class="processed-list">
          <div *ngFor="let doc of processedDocuments" class="processed-item">
            <mat-icon class="success-icon">check_circle</mat-icon>
            <div class="processed-info">
              <span class="processed-name">{{ doc.name }}</span>
              <small class="processed-id">ID: {{ doc.id }}</small>
            </div>
          </div>
        </div>
      </div>
    </div>
  `,
    styles: [`
    .selector-container {
      padding: 24px;
      max-width: 1400px;
      margin: 0 auto;
      max-height: 80vh;
      overflow-y: auto;
      background: #fafafa;
      border-radius: 12px;
    }
    
    .header {
      text-align: center;
      margin-bottom: 32px;
      padding-bottom: 24px;
      border-bottom: 2px solid #e0e0e0;
    }
    
    .header h2 {
      margin: 0 0 8px 0;
      color: #1976d2;
      font-size: 28px;
      font-weight: 500;
    }
    
    .subtitle {
      color: #666;
      font-size: 16px;
      margin: 0;
    }
    
    .loading-container {
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      padding: 60px 20px;
      color: #666;
    }
    
    .loading-container p {
      margin-top: 16px;
      font-size: 16px;
    }
    
    .documents-section {
      margin-bottom: 32px;
    }
    
    .section-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 24px;
      padding: 0 4px;
    }
    
    .section-header h3 {
      margin: 0;
      color: #333;
      font-size: 20px;
      font-weight: 500;
    }
    
    .count-badge {
      background: #1976d2;
      color: white;
      padding: 6px 12px;
      border-radius: 16px;
      font-size: 14px;
      font-weight: 500;
    }
    
    .count-badge.success {
      background: #4caf50;
    }
    
    .documents-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
      gap: 20px;
      margin-bottom: 24px;
    }
    
    .document-card {
      position: relative;
      transition: all 0.3s ease;
      border-radius: 12px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.1);
      overflow: hidden;
      background: white;
    }
    
    .document-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    
    .document-card.processing {
      opacity: 0.8;
      transform: scale(0.98);
    }
    
    .document-card.processed {
      border-left: 4px solid #4caf50;
    }
    
    .card-header {
      display: flex;
      align-items: flex-start;
      padding: 20px 20px 16px 20px;
      border-bottom: 1px solid #f0f0f0;
    }
    
    .document-icon {
      margin-right: 16px;
      color: #1976d2;
    }
    
    .document-icon mat-icon {
      font-size: 32px;
      width: 32px;
      height: 32px;
    }
    
    .document-info {
      flex: 1;
    }
    
    .document-title {
      margin: 0 0 8px 0;
      font-size: 16px;
      font-weight: 500;
      color: #333;
      line-height: 1.3;
    }
    
    .document-meta {
      display: flex;
      gap: 12px;
      margin: 0;
      font-size: 14px;
    }
    
    .file-size {
      color: #666;
      font-weight: 500;
    }
    
    .file-type {
      background: #e3f2fd;
      color: #1976d2;
      padding: 2px 8px;
      border-radius: 12px;
      font-size: 12px;
      font-weight: 500;
    }
    
    .card-content {
      padding: 16px 20px;
    }
    
    .document-description {
      margin: 0;
      color: #666;
      font-size: 14px;
      line-height: 1.4;
    }
    
    .card-actions {
      padding: 16px 20px 20px 20px;
      border-top: 1px solid #f0f0f0;
    }
    
    .process-button {
      width: 100%;
      height: 40px;
      font-weight: 500;
    }
    
    .processing-overlay {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(255, 255, 255, 0.95);
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 12px;
    }
    
    .processing-content {
      text-align: center;
      color: #1976d2;
    }
    
    .processing-content p {
      margin: 12px 0 4px 0;
      font-weight: 500;
    }
    
    .processing-content small {
      color: #666;
      font-size: 12px;
    }
    
    .no-documents {
      text-align: center;
      padding: 60px 20px;
    }
    
    .no-documents-content {
      color: #666;
    }
    
    .empty-icon {
      font-size: 64px;
      width: 64px;
      height: 64px;
      margin-bottom: 16px;
      color: #ccc;
    }
    
    .no-documents-content h3 {
      margin: 0 0 8px 0;
      color: #333;
    }
    
    .processed-summary {
      background: #f8f9fa;
      border-radius: 12px;
      padding: 24px;
      margin-top: 24px;
    }
    
    .summary-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 16px;
    }
    
    .summary-header h3 {
      margin: 0;
      color: #333;
      font-size: 18px;
    }
    
    .processed-list {
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    
    .processed-item {
      display: flex;
      align-items: center;
      padding: 12px;
      background: white;
      border-radius: 8px;
      border-left: 3px solid #4caf50;
    }
    
    .success-icon {
      color: #4caf50;
      margin-right: 12px;
    }
    
    .processed-info {
      flex: 1;
    }
    
    .processed-name {
      display: block;
      font-weight: 500;
      color: #333;
    }
    
    .processed-id {
      color: #666;
      font-size: 12px;
    }
    
    /* Scrollbar personalizado */
    .selector-container::-webkit-scrollbar {
      width: 8px;
    }
    
    .selector-container::-webkit-scrollbar-track {
      background: #f1f1f1;
      border-radius: 4px;
    }
    
    .selector-container::-webkit-scrollbar-thumb {
      background: #c1c1c1;
      border-radius: 4px;
    }
    
    .selector-container::-webkit-scrollbar-thumb:hover {
      background: #a8a8a8;
    }
  `]
})
export class DocumentSelectorComponent implements OnInit {
    @Output() documentProcessed = new EventEmitter<any>();

    availableDocuments: AvailableDocument[] = [];
    processedDocuments: any[] = [];
    isLoading = false;
    isProcessing = false;
    processingDocuments = new Set<string>();

    constructor(
        private knowledgeService: KnowledgeService,
        private snackBar: MatSnackBar
    ) { }

    ngOnInit() {
        this.loadAvailableDocuments();
        this.loadProcessedDocuments();
    }

    loadAvailableDocuments() {
        this.isLoading = true;

        this.knowledgeService.getAvailableDocuments().subscribe({
            next: (response) => {
                this.availableDocuments = response.documents;
                this.isLoading = false;
                console.log('Documentos disponibles:', this.availableDocuments);
            },
            error: (error) => {
                console.error('Error cargando documentos disponibles:', error);
                this.snackBar.open('Error cargando documentos disponibles', 'Cerrar', {
                    duration: 3000
                });
                this.isLoading = false;
            }
        });
    }

    loadProcessedDocuments() {
        this.knowledgeService.getAllDocuments().subscribe({
            next: (response) => {
                this.processedDocuments = response.documents.filter(doc => doc.status === 'completed');
                console.log('Documentos procesados cargados:', this.processedDocuments);
            },
            error: (error) => {
                console.error('Error cargando documentos procesados:', error);
            }
        });
    }

    processDocument(doc: AvailableDocument) {
        if (this.isProcessing || this.processingDocuments.has(doc.name)) {
            return;
        }

        this.processingDocuments.add(doc.name);
        this.isProcessing = true;

        this.knowledgeService.processExistingDocument(doc.name).subscribe({
            next: (response) => {
                console.log('Documento procesado:', response);

                this.processingDocuments.delete(doc.name);
                this.isProcessing = false;

                // Recargar documentos procesados
                this.loadProcessedDocuments();

                this.snackBar.open(`Documento ${doc.display_name} procesado exitosamente`, 'Cerrar', {
                    duration: 3000,
                    panelClass: ['success-snackbar']
                });

                this.documentProcessed.emit(response);
            },
            error: (error) => {
                console.error('Error procesando documento:', error);
                this.processingDocuments.delete(doc.name);
                this.isProcessing = false;

                this.snackBar.open(`Error procesando ${doc.display_name}: ${error.error?.detail || error.message}`, 'Cerrar', {
                    duration: 5000,
                    panelClass: ['error-snackbar']
                });
            }
        });
    }

    trackByDocumentName(index: number, doc: AvailableDocument): string {
        return doc.name;
    }

    isDocumentProcessed(docName: string): boolean {
        return this.processedDocuments.some(doc => doc.name === docName);
    }

    getDocumentDescription(docName: string): string {
        const descriptions: { [key: string]: string } = {
            'NS-Design.pdf': 'Manual de usuario de NS-Design, herramienta central de NS-DK para crear interfaces gráficas',
            'UserManual.pdf': 'Manual de usuario completo del sistema NS-DK',
            'NS-Report.pdf': 'Documentación del módulo de reportes NS-Report',
            'NS-Calc.pdf': 'Guía para el componente de cálculos NS-Calc',
            'Controls.pdf': 'Documentación de controles y componentes de interfaz',
            'controles.pdf': 'Guía de controles en español',
            'Bases_de_donnees.pdf': 'Documentación sobre acceso a bases de datos',
            'CommunicationAPIs.pdf': 'APIs de comunicación del sistema',
            'KernelAPIs.pdf': 'APIs del kernel del sistema NS-DK',
            'GUIandPrintingAPIs.pdf': 'APIs para interfaz gráfica e impresión',
            'Langage_NCL.pdf': 'Guía del lenguaje de programación NCL',
            'NCLLanguageGuide.pdf': 'Manual completo del lenguaje NCL',
            'Bibliotheque_de_services.pdf': 'Biblioteca de servicios del sistema',
            'Bibliotheques_IHM_et_Impression.pdf': 'Bibliotecas de interfaz e impresión',
            'Bibliotheques_de_communication.pdf': 'Bibliotecas de comunicación',
            'Bibliotheques_standards.pdf': 'Bibliotecas estándar del sistema',
            'InstallationGuide.pdf': 'Guía de instalación del sistema',
            'NewFeatures.pdf': 'Nuevas características y funcionalidades',
            'Release_description_NSDK7.0.pdf': 'Descripción de la versión 7.0',
            'Release_description_NSDK8.0.pdf': 'Descripción de la versión 8.0'
        };

        return descriptions[docName] || 'Documento técnico de NS-DK para consulta durante el análisis de IA';
    }
}
