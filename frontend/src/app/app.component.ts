import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterOutlet } from '@angular/router';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { MatIconModule } from '@angular/material/icon';
import { MatButtonModule } from '@angular/material/button';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [
    CommonModule,
    RouterOutlet,
    MatToolbarModule,
    MatSidenavModule,
    MatListModule,
    MatIconModule,
    MatButtonModule
  ],
  template: `
    <mat-sidenav-container class="sidenav-container">
      <mat-sidenav #drawer class="sidenav" fixedInViewport mode="side" opened>
        <mat-toolbar>
          <mat-icon>code</mat-icon>
          <span class="toolbar-spacer"></span>
          <span>Prompt Maestro</span>
        </mat-toolbar>
        
        <mat-nav-list>
          <mat-list-item routerLink="/dashboard" routerLinkActive="active">
            <mat-icon matListItemIcon>dashboard</mat-icon>
            <span matListItemTitle>Dashboard</span>
          </mat-list-item>
          
          <mat-list-item routerLink="/modules" routerLinkActive="active">
            <mat-icon matListItemIcon>folder</mat-icon>
            <span matListItemTitle>Módulos</span>
          </mat-list-item>
          
          <mat-list-item routerLink="/config" routerLinkActive="active">
            <mat-icon matListItemIcon>settings</mat-icon>
            <span matListItemTitle>Configuración</span>
          </mat-list-item>
          
          <mat-list-item routerLink="/knowledge" routerLinkActive="active">
            <mat-icon matListItemIcon>library_books</mat-icon>
            <span matListItemTitle>Conocimiento</span>
          </mat-list-item>
          
          <mat-divider></mat-divider>
          
          <mat-list-item>
            <mat-icon matListItemIcon>help</mat-icon>
            <span matListItemTitle>Ayuda</span>
          </mat-list-item>
        </mat-nav-list>
      </mat-sidenav>
      
      <mat-sidenav-content>
        <mat-toolbar color="primary">
          <button
            type="button"
            mat-icon-button
            (click)="drawer.toggle()"
            class="drawer-toggle">
            <mat-icon>menu</mat-icon>
          </button>
          
          <span>{{ title }}</span>
          
          <span class="toolbar-spacer"></span>
          
          <button mat-icon-button [matMenuTriggerFor]="menu">
            <mat-icon>account_circle</mat-icon>
          </button>
        </mat-toolbar>
        
        <main class="main-content">
          <router-outlet></router-outlet>
        </main>
      </mat-sidenav-content>
    </mat-sidenav-container>
  `,
  styles: [`
    .sidenav-container {
      height: 100vh;
    }
    
    .sidenav {
      width: 250px;
    }
    
    .sidenav .mat-toolbar {
      background: inherit;
    }
    
    .toolbar-spacer {
      flex: 1 1 auto;
    }
    
    .main-content {
      padding: 20px;
      height: calc(100vh - 64px);
      overflow: auto;
    }
    
    .drawer-toggle {
      display: none;
    }
    
    .mat-nav-list .mat-list-item.active {
      background-color: rgba(0, 0, 0, 0.1);
    }
    
    @media (max-width: 768px) {
      .sidenav {
        width: 100%;
      }
      
      .drawer-toggle {
        display: block;
      }
    }
  `]
})
export class AppComponent {
  title = 'Prompt Maestro';
}