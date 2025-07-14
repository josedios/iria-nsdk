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
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
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