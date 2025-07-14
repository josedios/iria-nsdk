import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';

interface DashboardStats {
  totalModules: number;
  completedModules: number;
  totalScreens: number;
  analyzedScreens: number;
  generatedScreens: number;
  migrationProgress: number;
}

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    MatCardModule,
    MatIconModule,
    MatProgressBarModule,
    MatGridListModule,
    MatButtonModule,
    MatChipsModule
  ],
  template: `
    <div class="dashboard-container">
      <h1 class="dashboard-title">Dashboard de Migración</h1>
      
      <mat-grid-list cols="4" rowHeight="150px" gutterSize="20px" class="stats-grid">
        <mat-grid-tile>
          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-content">
                <mat-icon class="stat-icon modules">folder</mat-icon>
                <div class="stat-info">
                  <h3>{{ stats.totalModules }}</h3>
                  <p>Módulos Totales</p>
                </div>
              </div>
            </mat-card-content>
          </mat-card>
        </mat-grid-tile>
        
        <mat-grid-tile>
          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-content">
                <mat-icon class="stat-icon screens">visibility</mat-icon>
                <div class="stat-info">
                  <h3>{{ stats.totalScreens }}</h3>
                  <p>Pantallas Totales</p>
                </div>
              </div>
            </mat-card-content>
          </mat-card>
        </mat-grid-tile>
        
        <mat-grid-tile>
          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-content">
                <mat-icon class="stat-icon analyzed">analytics</mat-icon>
                <div class="stat-info">
                  <h3>{{ stats.analyzedScreens }}</h3>
                  <p>Analizadas</p>
                </div>
              </div>
            </mat-card-content>
          </mat-card>
        </mat-grid-tile>
        
        <mat-grid-tile>
          <mat-card class="stat-card">
            <mat-card-content>
              <div class="stat-content">
                <mat-icon class="stat-icon generated">code</mat-icon>
                <div class="stat-info">
                  <h3>{{ stats.generatedScreens }}</h3>
                  <p>Generadas</p>
                </div>
              </div>
            </mat-card-content>
          </mat-card>
        </mat-grid-tile>
      </mat-grid-list>
      
      <div class="dashboard-content">
        <div class="left-panel">
          <mat-card class="progress-card">
            <mat-card-header>
              <mat-card-title>Progreso de Migración</mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="progress-info">
                <h2>{{ stats.migrationProgress }}%</h2>
                <p>Completado</p>
              </div>
              <mat-progress-bar 
                mode="determinate" 
                [value]="stats.migrationProgress"
                class="progress-bar">
              </mat-progress-bar>
              <div class="progress-details">
                <div class="detail-item">
                  <span>Módulos completados:</span>
                  <span>{{ stats.completedModules }}/{{ stats.totalModules }}</span>
                </div>
                <div class="detail-item">
                  <span>Pantallas migradas:</span>
                  <span>{{ stats.generatedScreens }}/{{ stats.totalScreens }}</span>
                </div>
              </div>
            </mat-card-content>
          </mat-card>
          
          <mat-card class="recent-activity">
            <mat-card-header>
              <mat-card-title>Actividad Reciente</mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="activity-item" *ngFor="let activity of recentActivity">
                <mat-icon [class]="'activity-icon ' + activity.type">{{ activity.icon }}</mat-icon>
                <div class="activity-content">
                  <p>{{ activity.message }}</p>
                  <span class="activity-time">{{ activity.timestamp }}</span>
                </div>
              </div>
            </mat-card-content>
          </mat-card>
        </div>
        
        <div class="right-panel">
          <mat-card class="quick-actions">
            <mat-card-header>
              <mat-card-title>Acciones Rápidas</mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="actions-grid">
                <button mat-raised-button color="primary" class="action-button">
                  <mat-icon>settings</mat-icon>
                  Configurar Proyecto
                </button>
                
                <button mat-raised-button color="accent" class="action-button">
                  <mat-icon>upload</mat-icon>
                  Vectorizar Código
                </button>
                
                <button mat-raised-button class="action-button">
                  <mat-icon>analytics</mat-icon>
                  Analizar Pantalla
                </button>
                
                <button mat-raised-button class="action-button">
                  <mat-icon>code</mat-icon>
                  Generar Código
                </button>
              </div>
            </mat-card-content>
          </mat-card>
          
          <mat-card class="system-status">
            <mat-card-header>
              <mat-card-title>Estado del Sistema</mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="status-item">
                <mat-chip selected="true" color="primary">
                  <mat-icon>check_circle</mat-icon>
                  Base de Datos
                </mat-chip>
              </div>
              <div class="status-item">
                <mat-chip selected="true" color="accent">
                  <mat-icon>cloud</mat-icon>
                  Vector Store
                </mat-chip>
              </div>
              <div class="status-item">
                <mat-chip selected="true" color="warn">
                  <mat-icon>psychology</mat-icon>
                  LLM Service
                </mat-chip>
              </div>
            </mat-card-content>
          </mat-card>
        </div>
      </div>
    </div>
  `,
  styles: [`
    .dashboard-container {
      padding: 20px;
    }
    
    .dashboard-title {
      margin-bottom: 30px;
      color: #333;
      font-weight: 300;
    }
    
    .stats-grid {
      margin-bottom: 30px;
    }
    
    .stat-card {
      width: 100%;
      height: 100%;
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
      font-size: 40px;
      width: 40px;
      height: 40px;
    }
    
    .stat-icon.modules { color: #2196F3; }
    .stat-icon.screens { color: #4CAF50; }
    .stat-icon.analyzed { color: #FF9800; }
    .stat-icon.generated { color: #9C27B0; }
    
    .stat-info h3 {
      margin: 0;
      font-size: 28px;
      font-weight: 500;
    }
    
    .stat-info p {
      margin: 5px 0 0 0;
      color: #666;
      font-size: 14px;
    }
    
    .dashboard-content {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 20px;
    }
    
    .left-panel, .right-panel {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    
    .progress-card {
      padding: 20px;
    }
    
    .progress-info {
      text-align: center;
      margin-bottom: 20px;
    }
    
    .progress-info h2 {
      margin: 0;
      font-size: 48px;
      font-weight: 300;
      color: #2196F3;
    }
    
    .progress-bar {
      height: 10px;
      border-radius: 5px;
      margin-bottom: 20px;
    }
    
    .progress-details {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    
    .detail-item {
      display: flex;
      justify-content: space-between;
      padding: 5px 0;
      border-bottom: 1px solid #eee;
    }
    
    .recent-activity {
      flex: 1;
    }
    
    .activity-item {
      display: flex;
      align-items: center;
      gap: 15px;
      padding: 10px 0;
      border-bottom: 1px solid #eee;
    }
    
    .activity-item:last-child {
      border-bottom: none;
    }
    
    .activity-icon {
      font-size: 20px;
      width: 20px;
      height: 20px;
    }
    
    .activity-icon.success { color: #4CAF50; }
    .activity-icon.warning { color: #FF9800; }
    .activity-icon.info { color: #2196F3; }
    
    .activity-content {
      flex: 1;
    }
    
    .activity-content p {
      margin: 0;
      font-size: 14px;
    }
    
    .activity-time {
      font-size: 12px;
      color: #666;
    }
    
    .quick-actions {
      padding: 20px;
    }
    
    .actions-grid {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 15px;
    }
    
    .action-button {
      display: flex;
      flex-direction: column;
      gap: 5px;
      padding: 20px;
      height: 80px;
    }
    
    .system-status {
      padding: 20px;
    }
    
    .status-item {
      margin-bottom: 10px;
    }
    
    .status-item mat-chip {
      display: flex;
      align-items: center;
      gap: 5px;
    }
    
    @media (max-width: 768px) {
      .stats-grid {
        grid-template-columns: 1fr 1fr;
      }
      
      .dashboard-content {
        grid-template-columns: 1fr;
      }
      
      .actions-grid {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class DashboardComponent implements OnInit {
  stats: DashboardStats = {
    totalModules: 45,
    completedModules: 12,
    totalScreens: 234,
    analyzedScreens: 156,
    generatedScreens: 89,
    migrationProgress: 38
  };
  
  recentActivity = [
    {
      type: 'success',
      icon: 'check_circle',
      message: 'Módulo "Facturación" migrado exitosamente',
      timestamp: 'Hace 2 horas'
    },
    {
      type: 'info',
      icon: 'analytics',
      message: 'Análisis completado para 15 pantallas',
      timestamp: 'Hace 4 horas'
    },
    {
      type: 'warning',
      icon: 'warning',
      message: 'Error en vectorización del módulo "Inventario"',
      timestamp: 'Hace 6 horas'
    },
    {
      type: 'success',
      icon: 'upload',
      message: 'Código NSDK vectorizado correctamente',
      timestamp: 'Hace 1 día'
    }
  ];
  
  ngOnInit() {
    // Aquí cargarían los datos reales desde el backend
  }
}