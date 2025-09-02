import { CommonModule } from '@angular/common';
import { Component, Inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatSnackBar } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { firstValueFrom } from 'rxjs';

@Component({
  selector: 'app-ai-analysis-modal',
  standalone: true,
  imports: [CommonModule, MatTabsModule, MatCardModule, MatChipsModule, MatButtonModule, MatIconModule, MatDividerModule],
  templateUrl: './ai-analysis-modal.component.html',
  styleUrls: ['./ai-analysis-modal.component.scss']
})
export class AIAnalysisModalComponent {
  constructor(
    public dialogRef: MatDialogRef<AIAnalysisModalComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private http: HttpClient,
    private snackBar: MatSnackBar
  ) { }

  getComplexityColor(complexity: string): string {
    const colors = { 'low': 'primary', 'medium': 'accent', 'high': 'warn' };
    return colors[complexity as keyof typeof colors] || 'default';
  }

  getComplexityLabel(complexity: string): string {
    const labels = { 'low': 'Baja', 'medium': 'Media', 'high': 'Alta' };
    return labels[complexity as keyof typeof labels] || complexity || 'N/A';
  }

  getFileTypeLabel(fileType: string): string {
    const labels = { 'screen': 'Pantalla', 'form': 'Formulario', 'report': 'Reporte', 'utility': 'Utilidad' };
    return labels[fileType as keyof typeof labels] || fileType || 'N/A';
  }

  getButtonColor(action: string): string {
    const colors = { 'save': 'primary', 'delete': 'warn', 'cancel': 'default', 'search': 'accent' };
    return colors[action as keyof typeof colors] || 'default';
  }

  getMethodColor(method: string): string {
    const colors = { 'GET': 'primary', 'POST': 'accent', 'PUT': 'warn', 'DELETE': 'warn' };
    return colors[method as keyof typeof colors] || 'default';
  }

  async generateCode() {
    try {
      console.log('Iniciando generación de código desde modal para:', this.data.node.name);

      // Llamar al endpoint de generación de código
      const response = await firstValueFrom(
        this.http.post<{ success: boolean, branch_name: string, message?: string }>(
          `http://localhost:8000/repositories/nsdk-sources/files/${this.data.node.id}/generate-code`,
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

        // Cerrar modal
        this.dialogRef.close();

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
    }
  }

  exportAnalysis() {
    console.log('Exportando análisis IA...');
    // TODO: Implementar exportación
  }

  // Métodos para manejar datos que pueden venir como strings JSON
  getDependencies(): string[] {
    try {
      if (typeof this.data.analysis.frontend_analysis?.dependencies === 'string') {
        return JSON.parse(this.data.analysis.frontend_analysis.dependencies);
      }
      return this.data.analysis.frontend_analysis?.dependencies || [];
    } catch (e) {
      console.warn('Error parsing dependencies:', e);
      return [];
    }
  }

  getMigrationNotes(): string[] {
    try {
      if (typeof this.data.analysis.migration_notes === 'string') {
        return JSON.parse(this.data.analysis.migration_notes);
      }
      return this.data.analysis.migration_notes || [];
    } catch (e) {
      console.warn('Error parsing migration_notes:', e);
      return [];
    }
  }

  getPotentialIssues(): string[] {
    try {
      if (typeof this.data.analysis.potential_issues === 'string') {
        return JSON.parse(this.data.analysis.potential_issues);
      }
      return this.data.analysis.potential_issues || [];
    } catch (e) {
      console.warn('Error parsing potential_issues:', e);
      return [];
    }
  }
}
