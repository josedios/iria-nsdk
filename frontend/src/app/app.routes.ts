import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    redirectTo: '/login',
    pathMatch: 'full'
  },
  {
    path: 'login',
    loadComponent: () => import('./features/login/login.component').then(m => m.LoginComponent)
  },
  {
    path: 'dashboard',
    loadComponent: () => import('./features/dashboard/dashboard.component').then(m => m.DashboardComponent)
  },
  {
    path: 'modules',
    loadComponent: () => import('./features/modules/modules.component').then(m => m.ModulesComponent)
  },
  {
    path: 'config',
    loadComponent: () => import('./features/config/config.component').then(m => m.ConfigComponent)
  },
  {
    path: 'knowledge',
    loadComponent: () => import('./features/knowledge/knowledge.component').then(m => m.KnowledgeComponent)
  },
  {
    path: '**',
    redirectTo: '/login'
  }
];