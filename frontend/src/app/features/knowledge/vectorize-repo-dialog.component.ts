import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';

export interface VectorizeRepoDialogData {
    repo_url: string;
    branch: string;
    username?: string;
    token?: string;
}

@Component({
    selector: 'app-vectorize-repo-dialog',
    standalone: true,
    imports: [
        CommonModule,
        FormsModule,
        MatDialogModule,
        MatFormFieldModule,
        MatInputModule,
        MatButtonModule,
        MatSelectModule,
        MatIconModule
    ],
    template: `
    <h2 mat-dialog-title>
      <mat-icon>upload</mat-icon>
      Vectorizar Repositorio NSDK
    </h2>
    
    <mat-dialog-content>
      <div class="dialog-content">
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>URL del Repositorio</mat-label>
          <input matInput 
                 [(ngModel)]="data.repo_url" 
                 placeholder="https://github.com/usuario/repo-nsdk"
                 required>
          <mat-icon matSuffix>link</mat-icon>
        </mat-form-field>
        
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Rama</mat-label>
          <mat-select [(ngModel)]="data.branch">
            <mat-option value="main">main</mat-option>
            <mat-option value="master">master</mat-option>
            <mat-option value="develop">develop</mat-option>
            <mat-option value="dev">dev</mat-option>
          </mat-select>
        </mat-form-field>
        
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Usuario (opcional)</mat-label>
          <input matInput 
                 [(ngModel)]="data.username" 
                 placeholder="usuario">
          <mat-icon matSuffix>person</mat-icon>
        </mat-form-field>
        
        <mat-form-field appearance="outline" class="full-width">
          <mat-label>Token de Acceso (opcional)</mat-label>
          <input matInput 
                 [(ngModel)]="data.token" 
                 placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                 type="password">
          <mat-icon matSuffix>vpn_key</mat-icon>
        </mat-form-field>
        
        <div class="info-box">
          <mat-icon>info</mat-icon>
          <p>
            <strong>Nota:</strong> El sistema procesará automáticamente todos los archivos 
            .SCR, .NCL, .INC y .PRG del repositorio para crear embeddings vectoriales 
            que permitan búsquedas semánticas.
          </p>
        </div>
      </div>
    </mat-dialog-content>
    
    <mat-dialog-actions align="end">
      <button mat-button (click)="onCancel()">
        <mat-icon>cancel</mat-icon>
        Cancelar
      </button>
      <button mat-raised-button 
              color="primary" 
              (click)="onConfirm()"
              [disabled]="!data.repo_url.trim()">
        <mat-icon>upload</mat-icon>
        Iniciar Vectorización
      </button>
    </mat-dialog-actions>
  `,
    styles: [`
    .dialog-content {
      min-width: 400px;
    }
    
    .full-width {
      width: 100%;
      margin-bottom: 16px;
    }
    
    .info-box {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 16px;
      background-color: #e3f2fd;
      border-radius: 8px;
      margin-top: 16px;
    }
    
    .info-box mat-icon {
      color: #1976d2;
      margin-top: 2px;
    }
    
    .info-box p {
      margin: 0;
      color: #1976d2;
      font-size: 14px;
      line-height: 1.4;
    }
    
    mat-dialog-title {
      display: flex;
      align-items: center;
      gap: 12px;
    }
    
    mat-dialog-actions {
      padding: 16px 0;
    }
    
    @media (max-width: 600px) {
      .dialog-content {
        min-width: 300px;
      }
    }
  `]
})
export class VectorizeRepoDialogComponent {
    constructor(
        public dialogRef: MatDialogRef<VectorizeRepoDialogComponent>,
        @Inject(MAT_DIALOG_DATA) public data: VectorizeRepoDialogData
    ) { }

    onCancel(): void {
        this.dialogRef.close();
    }

    onConfirm(): void {
        this.dialogRef.close(this.data);
    }
}
