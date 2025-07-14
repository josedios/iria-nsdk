import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router } from '@angular/router';
import { MatCardModule } from '@angular/material/card';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule
  ],
  template: `
    <div class="login-container">
      <div class="login-background">
        <div class="background-pattern"></div>
      </div>
      
      <div class="login-content">
        <mat-card class="login-card">
          <mat-card-header class="login-header">
            <div class="brand">
              <mat-icon class="brand-icon">code</mat-icon>
              <h1>Prompt Maestro</h1>
            </div>
            <p class="subtitle">Migración NSDK hacia tecnologías modernas</p>
          </mat-card-header>
          
          <mat-card-content class="login-form">
            <div class="poc-notice">
              <mat-icon>info</mat-icon>
              <div class="notice-content">
                <h3>Versión PoC - Acceso Libre</h3>
                <p>Esta es una versión de demostración. Haz clic en "Acceder" para continuar.</p>
              </div>
            </div>
            
            <form class="form">
              <mat-form-field appearance="outline" class="form-field">
                <mat-label>Usuario (Opcional)</mat-label>
                <input matInput [(ngModel)]="username" name="username" placeholder="desarrollador@empresa.com">
                <mat-icon matSuffix>person</mat-icon>
              </mat-form-field>
              
              <mat-form-field appearance="outline" class="form-field">
                <mat-label>Contraseña (Opcional)</mat-label>
                <input matInput type="password" [(ngModel)]="password" name="password" placeholder="••••••••">
                <mat-icon matSuffix>lock</mat-icon>
              </mat-form-field>
              
              <button mat-raised-button color="primary" class="login-button" (click)="login()">
                <mat-icon>login</mat-icon>
                Acceder al Sistema
              </button>
              
              <button mat-button class="demo-button" (click)="loginAsDemo()">
                <mat-icon>play_arrow</mat-icon>
                Continuar como Demo
              </button>
            </form>
          </mat-card-content>
          
          <mat-card-footer class="login-footer">
            <div class="features">
              <div class="feature">
                <mat-icon>analytics</mat-icon>
                <span>Análisis con IA</span>
              </div>
              <div class="feature">
                <mat-icon>code</mat-icon>
                <span>Generación Automática</span>
              </div>
              <div class="feature">
                <mat-icon>git_commit</mat-icon>
                <span>Integración Git</span>
              </div>
            </div>
            
            <div class="version-info">
              <span>Prompt Maestro v1.0.0</span>
              <span>Construido con ❤️ para modernizar NSDK</span>
            </div>
          </mat-card-footer>
        </mat-card>
      </div>
    </div>
  `,
  styles: [`
    .login-container {
      height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
      overflow: hidden;
    }
    
    .login-background {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      z-index: -2;
    }
    
    .background-pattern {
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background-image: 
        radial-gradient(circle at 20% 50%, rgba(120, 119, 198, 0.3) 0%, transparent 50%),
        radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.3) 0%, transparent 50%),
        radial-gradient(circle at 40% 80%, rgba(120, 219, 255, 0.3) 0%, transparent 50%);
      z-index: -1;
    }
    
    .login-content {
      width: 100%;
      max-width: 450px;
      padding: 20px;
    }
    
    .login-card {
      padding: 0;
      border-radius: 16px;
      box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
      overflow: hidden;
      backdrop-filter: blur(10px);
      background: rgba(255, 255, 255, 0.95);
    }
    
    .login-header {
      text-align: center;
      padding: 40px 40px 20px 40px;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
    }
    
    .brand {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;
    }
    
    .brand-icon {
      font-size: 48px;
      width: 48px;
      height: 48px;
      background: rgba(255, 255, 255, 0.2);
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    
    .brand h1 {
      margin: 0;
      font-size: 28px;
      font-weight: 300;
      letter-spacing: -1px;
    }
    
    .subtitle {
      margin: 10px 0 0 0;
      opacity: 0.9;
      font-size: 14px;
      font-weight: 300;
    }
    
    .login-form {
      padding: 40px;
    }
    
    .poc-notice {
      display: flex;
      align-items: flex-start;
      gap: 15px;
      padding: 20px;
      background: linear-gradient(135deg, #e3f2fd 0%, #f3e5f5 100%);
      border-radius: 12px;
      margin-bottom: 30px;
      border-left: 4px solid #2196F3;
    }
    
    .poc-notice mat-icon {
      color: #2196F3;
      margin-top: 2px;
    }
    
    .notice-content h3 {
      margin: 0 0 5px 0;
      font-size: 16px;
      font-weight: 500;
      color: #1976D2;
    }
    
    .notice-content p {
      margin: 0;
      font-size: 14px;
      color: #424242;
      line-height: 1.4;
    }
    
    .form {
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    
    .form-field {
      width: 100%;
    }
    
    .login-button {
      height: 48px;
      font-size: 16px;
      font-weight: 500;
      border-radius: 8px;
      margin-top: 10px;
    }
    
    .demo-button {
      height: 40px;
      margin-top: 10px;
      color: #666;
    }
    
    .login-footer {
      padding: 30px 40px;
      background: #f8f9fa;
      border-top: 1px solid #e0e0e0;
    }
    
    .features {
      display: flex;
      justify-content: space-between;
      margin-bottom: 20px;
    }
    
    .feature {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 5px;
      flex: 1;
    }
    
    .feature mat-icon {
      color: #667eea;
      font-size: 20px;
    }
    
    .feature span {
      font-size: 12px;
      color: #666;
      text-align: center;
    }
    
    .version-info {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 5px;
      font-size: 12px;
      color: #999;
      text-align: center;
    }
    
    .version-info span:first-child {
      font-weight: 500;
      color: #666;
    }
    
    @media (max-width: 768px) {
      .login-content {
        padding: 10px;
      }
      
      .login-header,
      .login-form,
      .login-footer {
        padding: 30px 20px;
      }
      
      .brand h1 {
        font-size: 24px;
      }
      
      .features {
        flex-direction: column;
        gap: 15px;
      }
      
      .feature {
        flex-direction: row;
        justify-content: center;
        gap: 10px;
      }
    }
    
    @media (max-width: 480px) {
      .login-container {
        padding: 0;
      }
      
      .login-card {
        border-radius: 0;
        height: 100vh;
        display: flex;
        flex-direction: column;
      }
      
      .login-form {
        flex: 1;
        display: flex;
        flex-direction: column;
        justify-content: center;
      }
    }
  `]
})
export class LoginComponent {
  username = '';
  password = '';

  constructor(private router: Router) {}

  login() {
    // Simulación de login (PoC - siempre exitoso)
    console.log('Login attempt:', { username: this.username, password: this.password });
    
    // En una implementación real, aquí harías la validación con el backend
    // Para el PoC, simplemente redirigimos al dashboard
    this.router.navigate(['/dashboard']);
  }

  loginAsDemo() {
    // Acceso directo como demo
    console.log('Demo access');
    this.router.navigate(['/dashboard']);
  }
}