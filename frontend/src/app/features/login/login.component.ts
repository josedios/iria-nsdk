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
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.scss']
})
export class LoginComponent {
  username = '';
  password = '';

  constructor(private router: Router) {}

  login() {
    // En una implementación real, aquí iría la lógica de autenticación
    console.log('Iniciando sesión con:', { username: this.username, password: this.password });
    
    // Simular autenticación exitosa
    setTimeout(() => {
      this.router.navigate(['/dashboard']);
    }, 1000);
  }

  loginAsDemo() {
    console.log('Accediendo como demo');
    
    // Simular acceso demo
    setTimeout(() => {
      this.router.navigate(['/dashboard']);
    }, 500);
  }
}