import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, EventEmitter, Output } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSnackBar } from '@angular/material/snack-bar';
import { KnowledgeService } from './knowledge.service';

@Component({
    selector: 'app-document-upload',
    standalone: true,
    imports: [
        CommonModule,
        MatCardModule,
        MatButtonModule,
        MatIconModule,
        MatProgressBarModule
    ],
    template: `
    <div class="upload-container">
      <h3>Subir Documentación NSDK</h3>
      
      <div class="upload-section">
        <input 
          type="file" 
          #fileInput
          (change)="onFileSelected($event)" 
          accept=".pdf"
          style="display: none;"
        >
        
        <button 
          mat-raised-button 
          color="primary"
          (click)="fileInput.click()"
          [disabled]="isUploading"
        >
          <mat-icon>upload</mat-icon>
          Seleccionar PDF
        </button>
        
                 <span *ngIf="selectedFile" class="file-name">
           {{ selectedFile?.name }}
         </span>
      </div>
      
      <div *ngIf="selectedFile" class="upload-actions">
        <button 
          mat-raised-button 
          color="accent"
          (click)="uploadDocument()" 
          [disabled]="isUploading"
        >
          <mat-icon>cloud_upload</mat-icon>
          Procesar Documento
        </button>
        
        <button 
          mat-button 
          (click)="clearSelection()"
          [disabled]="isUploading"
        >
          Cancelar
        </button>
      </div>
      
      <div *ngIf="isUploading" class="upload-progress">
        <mat-progress-bar mode="indeterminate"></mat-progress-bar>
        <p>Procesando documento: {{ uploadProgress }}%</p>
      </div>
      
      <div *ngIf="uploadResult" class="upload-result">
        <mat-card>
          <mat-card-header>
            <mat-card-title>Resultado del Procesamiento</mat-card-title>
          </mat-card-header>
          <mat-card-content>
            <p><strong>Estado:</strong> {{ uploadResult.status }}</p>
            <p><strong>Documento:</strong> {{ uploadResult.document_name }}</p>
            <p><strong>ID:</strong> {{ uploadResult.document_id }}</p>
          </mat-card-content>
        </mat-card>
      </div>
    </div>
  `,
    styles: [`
    .upload-container {
      padding: 20px;
      max-width: 600px;
      margin: 0 auto;
    }
    
    .upload-section {
      margin: 20px 0;
      display: flex;
      align-items: center;
      gap: 15px;
    }
    
    .file-name {
      color: #666;
      font-style: italic;
    }
    
    .upload-actions {
      margin: 20px 0;
      display: flex;
      gap: 10px;
    }
    
    .upload-progress {
      margin: 20px 0;
    }
    
    .upload-result {
      margin: 20px 0;
    }
    
    mat-progress-bar {
      margin: 10px 0;
    }
  `]
})
export class DocumentUploadComponent {
    @Output() documentUploaded = new EventEmitter<any>();

    selectedFile: File | null = null;
    isUploading = false;
    uploadProgress = 0;
    uploadResult: any = null;

    constructor(
        private http: HttpClient,
        private snackBar: MatSnackBar,
        private knowledgeService: KnowledgeService
    ) { }

    onFileSelected(event: any): void {
        const file = event.target.files[0];
        if (file && file.type === 'application/pdf') {
            this.selectedFile = file;
            this.uploadResult = null;
        } else {
            this.snackBar.open('Por favor selecciona un archivo PDF válido', 'Cerrar', {
                duration: 3000
            });
        }
    }

    clearSelection(): void {
        this.selectedFile = null;
        this.uploadResult = null;
        this.uploadProgress = 0;
    }

    async uploadDocument(): Promise<void> {
        if (!this.selectedFile) {
            return;
        }

        this.isUploading = true;
        this.uploadProgress = 0;

        try {
            // Simular progreso
            const progressInterval = setInterval(() => {
                if (this.uploadProgress < 90) {
                    this.uploadProgress += Math.random() * 10;
                }
            }, 500);

            // Por ahora, simular el procesamiento
            // TODO: Implementar upload real cuando el backend soporte FormData
            await this.simulateDocumentProcessing();

            clearInterval(progressInterval);
            this.uploadProgress = 100;

            this.uploadResult = {
                status: 'success',
                document_name: this.selectedFile.name.replace('.pdf', ''),
                document_id: 'simulated-id-' + Date.now()
            };

            this.snackBar.open('Documento procesado exitosamente', 'Cerrar', {
                duration: 3000
            });

            this.documentUploaded.emit(this.uploadResult);

        } catch (error) {
            console.error('Error procesando documento:', error);
            this.snackBar.open('Error procesando documento', 'Cerrar', {
                duration: 3000
            });
        } finally {
            this.isUploading = false;
        }
    }

    private async simulateDocumentProcessing(): Promise<void> {
        // Simular el procesamiento del documento
        return new Promise((resolve) => {
            setTimeout(() => {
                resolve();
            }, 3000);
        });
    }
}
