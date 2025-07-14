import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatTabsModule } from '@angular/material/tabs';
import { MatSnackBarModule, MatSnackBar } from '@angular/material/snack-bar';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatDividerModule } from '@angular/material/divider';
import { MatChipsModule } from '@angular/material/chips';

interface Configuration {
  id?: string;
  name: string;
  sourceRepo: RepositoryConfig;
  targetRepo: RepositoryConfig;
  llmConfig: LLMConfig;
  vectorStoreConfig: VectorStoreConfig;
  isActive: boolean;
}

interface RepositoryConfig {
  url: string;
  branch: string;
  username?: string;
  token?: string;
  sshKey?: string;
}

interface LLMConfig {
  provider: 'openai' | 'ollama' | 'mistral';
  apiKey?: string;
  baseUrl?: string;
  modelName: string;
  temperature: number;
  maxTokens: number;
}

interface VectorStoreConfig {
  type: 'faiss' | 'qdrant' | 'chroma';
  connectionString?: string;
  collectionName: string;
  embeddingModel: string;
  dimension: number;
}

@Component({
  selector: 'app-config',
  standalone: true,
  imports: [
    CommonModule,
    ReactiveFormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatSnackBarModule,
    MatProgressSpinnerModule,
    MatSlideToggleModule,
    MatDividerModule,
    MatChipsModule
  ],
  template: `
    <div class="config-container">
      <div class="config-header">
        <h1>Configuración del Sistema</h1>
        <div class="header-actions">
          <button mat-raised-button color="accent" (click)="testConfiguration()" [disabled]="loading">
            <mat-icon>speed</mat-icon>
            Probar Conexiones
          </button>
          <button mat-raised-button color="primary" (click)="saveConfiguration()" [disabled]="!configForm.valid || loading">
            <mat-icon>save</mat-icon>
            Guardar Configuración
          </button>
        </div>
      </div>

      <form [formGroup]="configForm" class="config-form">
        <mat-tab-group class="config-tabs">
          <!-- Configuración General -->
          <mat-tab label="General">
            <div class="tab-content">
              <mat-card>
                <mat-card-header>
                  <mat-card-title>Información General</mat-card-title>
                  <mat-card-subtitle>Configuración básica del proyecto</mat-card-subtitle>
                </mat-card-header>
                <mat-card-content>
                  <div class="form-row">
                    <mat-form-field appearance="outline" class="full-width">
                      <mat-label>Nombre del Proyecto</mat-label>
                      <input matInput formControlName="name" placeholder="Migración NSDK - Cliente X">
                      <mat-icon matSuffix>business</mat-icon>
                    </mat-form-field>
                  </div>
                  
                  <div class="form-row">
                    <mat-slide-toggle formControlName="isActive" color="primary">
                      Configuración Activa
                    </mat-slide-toggle>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>
          </mat-tab>

          <!-- Repositorios -->
          <mat-tab label="Repositorios">
            <div class="tab-content">
              <!-- Repositorio Origen -->
              <mat-card class="repo-card">
                <mat-card-header>
                  <mat-card-title>
                    <mat-icon>folder_open</mat-icon>
                    Repositorio Origen (NSDK)
                  </mat-card-title>
                  <mat-card-subtitle>Configuración del repositorio con código NSDK legacy</mat-card-subtitle>
                </mat-card-header>
                <mat-card-content formGroupName="sourceRepo">
                  <div class="form-row">
                    <mat-form-field appearance="outline" class="full-width">
                      <mat-label>URL del Repositorio</mat-label>
                      <input matInput formControlName="url" placeholder="https://github.com/empresa/nsdk-legacy.git">
                      <mat-icon matSuffix>link</mat-icon>
                    </mat-form-field>
                  </div>
                  
                  <div class="form-row">
                    <mat-form-field appearance="outline">
                      <mat-label>Rama Principal</mat-label>
                      <input matInput formControlName="branch" placeholder="main">
                    </mat-form-field>
                    
                    <mat-form-field appearance="outline">
                      <mat-label>Usuario</mat-label>
                      <input matInput formControlName="username" placeholder="usuario-git">
                    </mat-form-field>
                  </div>
                  
                  <div class="form-row">
                    <mat-form-field appearance="outline" class="full-width">
                      <mat-label>Token de Acceso</mat-label>
                      <input matInput type="password" formControlName="token" placeholder="ghp_...">
                      <mat-icon matSuffix>vpn_key</mat-icon>
                    </mat-form-field>
                  </div>
                </mat-card-content>
              </mat-card>

              <!-- Repositorio Destino -->
              <mat-card class="repo-card">
                <mat-card-header>
                  <mat-card-title>
                    <mat-icon>folder_special</mat-icon>
                    Repositorio Destino (Angular/Spring Boot)
                  </mat-card-title>
                  <mat-card-subtitle>Configuración del repositorio donde se generará el código moderno</mat-card-subtitle>
                </mat-card-header>
                <mat-card-content formGroupName="targetRepo">
                  <div class="form-row">
                    <mat-form-field appearance="outline" class="full-width">
                      <mat-label>URL del Repositorio</mat-label>
                      <input matInput formControlName="url" placeholder="https://github.com/empresa/app-moderna.git">
                      <mat-icon matSuffix>link</mat-icon>
                    </mat-form-field>
                  </div>
                  
                  <div class="form-row">
                    <mat-form-field appearance="outline">
                      <mat-label>Rama Principal</mat-label>
                      <input matInput formControlName="branch" placeholder="main">
                    </mat-form-field>
                    
                    <mat-form-field appearance="outline">
                      <mat-label>Usuario</mat-label>
                      <input matInput formControlName="username" placeholder="usuario-git">
                    </mat-form-field>
                  </div>
                  
                  <div class="form-row">
                    <mat-form-field appearance="outline" class="full-width">
                      <mat-label>Token de Acceso</mat-label>
                      <input matInput type="password" formControlName="token" placeholder="ghp_...">
                      <mat-icon matSuffix>vpn_key</mat-icon>
                    </mat-form-field>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>
          </mat-tab>

          <!-- LLM Configuration -->
          <mat-tab label="Inteligencia Artificial">
            <div class="tab-content">
              <mat-card>
                <mat-card-header>
                  <mat-card-title>
                    <mat-icon>psychology</mat-icon>
                    Configuración del LLM
                  </mat-card-title>
                  <mat-card-subtitle>Configura el proveedor de IA para análisis y generación de código</mat-card-subtitle>
                </mat-card-header>
                <mat-card-content formGroupName="llmConfig">
                  <div class="form-row">
                    <mat-form-field appearance="outline">
                      <mat-label>Proveedor de IA</mat-label>
                      <mat-select formControlName="provider" (selectionChange)="onProviderChange($event.value)">
                        <mat-option value="openai">OpenAI (GPT-4)</mat-option>
                        <mat-option value="ollama">Ollama (Local)</mat-option>
                        <mat-option value="mistral">Mistral AI</mat-option>
                      </mat-select>
                      <mat-icon matSuffix>smart_toy</mat-icon>
                    </mat-form-field>
                    
                    <mat-form-field appearance="outline">
                      <mat-label>Modelo</mat-label>
                      <mat-select formControlName="modelName">
                        <mat-option *ngFor="let model of availableModels" [value]="model.value">
                          {{ model.label }}
                        </mat-option>
                      </mat-select>
                    </mat-form-field>
                  </div>
                  
                  <div class="form-row" *ngIf="showApiKey">
                    <mat-form-field appearance="outline" class="full-width">
                      <mat-label>API Key</mat-label>
                      <input matInput type="password" formControlName="apiKey" [placeholder]="apiKeyPlaceholder">
                      <mat-icon matSuffix>key</mat-icon>
                    </mat-form-field>
                  </div>
                  
                  <div class="form-row" *ngIf="showBaseUrl">
                    <mat-form-field appearance="outline" class="full-width">
                      <mat-label>URL Base</mat-label>
                      <input matInput formControlName="baseUrl" placeholder="http://localhost:11434">
                      <mat-icon matSuffix>link</mat-icon>
                    </mat-form-field>
                  </div>
                  
                  <mat-divider></mat-divider>
                  
                  <h4>Parámetros de Generación</h4>
                  <div class="form-row">
                    <mat-form-field appearance="outline">
                      <mat-label>Temperatura (0.0 - 1.0)</mat-label>
                      <input matInput type="number" formControlName="temperature" min="0" max="1" step="0.1">
                      <mat-hint>Controla la creatividad del modelo</mat-hint>
                    </mat-form-field>
                    
                    <mat-form-field appearance="outline">
                      <mat-label>Máximo Tokens</mat-label>
                      <input matInput type="number" formControlName="maxTokens" min="1000" max="8000">
                      <mat-hint>Límite de tokens por respuesta</mat-hint>
                    </mat-form-field>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>
          </mat-tab>

          <!-- Vector Store -->
          <mat-tab label="Vector Store">
            <div class="tab-content">
              <mat-card>
                <mat-card-header>
                  <mat-card-title>
                    <mat-icon>storage</mat-icon>
                    Configuración del Vector Store
                  </mat-card-title>
                  <mat-card-subtitle>Almacenamiento vectorial para búsqueda semántica de código</mat-card-subtitle>
                </mat-card-header>
                <mat-card-content formGroupName="vectorStoreConfig">
                  <div class="form-row">
                    <mat-form-field appearance="outline">
                      <mat-label>Tipo de Vector Store</mat-label>
                      <mat-select formControlName="type" (selectionChange)="onVectorStoreChange($event.value)">
                        <mat-option value="faiss">FAISS (Local)</mat-option>
                        <mat-option value="qdrant">Qdrant (Distribuido)</mat-option>
                        <mat-option value="chroma">Chroma (Embebido)</mat-option>
                      </mat-select>
                      <mat-icon matSuffix>database</mat-icon>
                    </mat-form-field>
                    
                    <mat-form-field appearance="outline">
                      <mat-label>Nombre de Colección</mat-label>
                      <input matInput formControlName="collectionName" placeholder="nsdk_migration">
                    </mat-form-field>
                  </div>
                  
                  <div class="form-row" *ngIf="showConnectionString">
                    <mat-form-field appearance="outline" class="full-width">
                      <mat-label>Cadena de Conexión</mat-label>
                      <input matInput formControlName="connectionString" [placeholder]="connectionStringPlaceholder">
                      <mat-icon matSuffix>link</mat-icon>
                    </mat-form-field>
                  </div>
                  
                  <div class="form-row">
                    <mat-form-field appearance="outline">
                      <mat-label>Modelo de Embeddings</mat-label>
                      <mat-select formControlName="embeddingModel">
                        <mat-option value="text-embedding-3-small">OpenAI text-embedding-3-small</mat-option>
                        <mat-option value="text-embedding-3-large">OpenAI text-embedding-3-large</mat-option>
                        <mat-option value="sentence-transformers">Sentence Transformers</mat-option>
                      </mat-select>
                    </mat-form-field>
                    
                    <mat-form-field appearance="outline">
                      <mat-label>Dimensiones</mat-label>
                      <input matInput type="number" formControlName="dimension" readonly>
                    </mat-form-field>
                  </div>
                </mat-card-content>
              </mat-card>
            </div>
          </mat-tab>
        </mat-tab-group>
      </form>

      <!-- Estado de Conexiones -->
      <mat-card class="status-card" *ngIf="connectionStatus">
        <mat-card-header>
          <mat-card-title>Estado de Conexiones</mat-card-title>
        </mat-card-header>
        <mat-card-content>
          <div class="status-grid">
            <div class="status-item" *ngFor="let status of connectionStatus">
              <mat-icon [class]="'status-icon ' + status.status">
                {{ status.status === 'success' ? 'check_circle' : status.status === 'error' ? 'error' : 'hourglass_empty' }}
              </mat-icon>
              <div class="status-info">
                <h4>{{ status.service }}</h4>
                <p [class]="'status-text ' + status.status">{{ status.message }}</p>
              </div>
            </div>
          </div>
        </mat-card-content>
      </mat-card>
    </div>
  `,
  styles: [`
    .config-container {
      padding: 20px;
      max-width: 1200px;
      margin: 0 auto;
    }
    
    .config-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 30px;
    }
    
    .config-header h1 {
      margin: 0;
      color: #333;
      font-weight: 300;
    }
    
    .header-actions {
      display: flex;
      gap: 10px;
    }
    
    .config-form {
      margin-bottom: 30px;
    }
    
    .config-tabs {
      width: 100%;
    }
    
    .tab-content {
      padding: 20px 0;
    }
    
    .repo-card, .status-card {
      margin-bottom: 20px;
    }
    
    .form-row {
      display: flex;
      gap: 20px;
      margin-bottom: 20px;
    }
    
    .form-row mat-form-field {
      flex: 1;
    }
    
    .full-width {
      width: 100%;
    }
    
    .status-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
      gap: 20px;
    }
    
    .status-item {
      display: flex;
      align-items: center;
      gap: 15px;
      padding: 15px;
      border-radius: 8px;
      background-color: #f8f9fa;
    }
    
    .status-icon {
      font-size: 24px;
      width: 24px;
      height: 24px;
    }
    
    .status-icon.success { color: #4CAF50; }
    .status-icon.error { color: #f44336; }
    .status-icon.testing { color: #FF9800; }
    
    .status-info h4 {
      margin: 0 0 5px 0;
      font-size: 14px;
      font-weight: 500;
    }
    
    .status-text {
      margin: 0;
      font-size: 12px;
    }
    
    .status-text.success { color: #4CAF50; }
    .status-text.error { color: #f44336; }
    .status-text.testing { color: #FF9800; }
    
    mat-card-header mat-card-title {
      display: flex;
      align-items: center;
      gap: 10px;
    }
    
    mat-divider {
      margin: 20px 0;
    }
    
    @media (max-width: 768px) {
      .config-header {
        flex-direction: column;
        gap: 15px;
        align-items: flex-start;
      }
      
      .header-actions {
        width: 100%;
      }
      
      .form-row {
        flex-direction: column;
        gap: 10px;
      }
      
      .status-grid {
        grid-template-columns: 1fr;
      }
    }
  `]
})
export class ConfigComponent implements OnInit {
  configForm: FormGroup;
  loading = false;
  
  availableModels: {label: string, value: string}[] = [];
  showApiKey = true;
  showBaseUrl = false;
  apiKeyPlaceholder = 'sk-...';
  
  showConnectionString = false;
  connectionStringPlaceholder = '';
  
  connectionStatus: {service: string, status: 'success' | 'error' | 'testing', message: string}[] | null = null;

  constructor(
    private fb: FormBuilder,
    private snackBar: MatSnackBar
  ) {
    this.configForm = this.createForm();
  }

  ngOnInit() {
    this.loadConfiguration();
    this.onProviderChange('openai'); // Default
    this.onVectorStoreChange('faiss'); // Default
  }

  createForm(): FormGroup {
    return this.fb.group({
      name: ['Migración NSDK - Proyecto Principal', Validators.required],
      isActive: [true],
      sourceRepo: this.fb.group({
        url: ['', Validators.required],
        branch: ['main', Validators.required],
        username: [''],
        token: ['']
      }),
      targetRepo: this.fb.group({
        url: ['', Validators.required],
        branch: ['main', Validators.required],
        username: [''],
        token: ['']
      }),
      llmConfig: this.fb.group({
        provider: ['openai', Validators.required],
        apiKey: [''],
        baseUrl: [''],
        modelName: ['gpt-4', Validators.required],
        temperature: [0.7, [Validators.min(0), Validators.max(1)]],
        maxTokens: [4000, [Validators.min(1000), Validators.max(8000)]]
      }),
      vectorStoreConfig: this.fb.group({
        type: ['faiss', Validators.required],
        connectionString: [''],
        collectionName: ['nsdk_migration', Validators.required],
        embeddingModel: ['text-embedding-3-small', Validators.required],
        dimension: [1536]
      })
    });
  }

  onProviderChange(provider: string) {
    this.showApiKey = provider !== 'ollama';
    this.showBaseUrl = provider === 'ollama';
    
    switch (provider) {
      case 'openai':
        this.availableModels = [
          { label: 'GPT-4', value: 'gpt-4' },
          { label: 'GPT-4 Turbo', value: 'gpt-4-turbo-preview' },
          { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
        ];
        this.apiKeyPlaceholder = 'sk-...';
        break;
      
      case 'ollama':
        this.availableModels = [
          { label: 'Llama 2 7B', value: 'llama2' },
          { label: 'Llama 2 13B', value: 'llama2:13b' },
          { label: 'Mistral 7B', value: 'mistral' },
          { label: 'CodeLlama', value: 'codellama' }
        ];
        break;
      
      case 'mistral':
        this.availableModels = [
          { label: 'Mistral 7B Instruct', value: 'mistral-tiny' },
          { label: 'Mistral 8x7B', value: 'mistral-small' },
          { label: 'Mistral Medium', value: 'mistral-medium' }
        ];
        this.apiKeyPlaceholder = 'Mistral API Key';
        break;
    }
    
    // Actualizar modelo por defecto
    if (this.availableModels.length > 0) {
      this.configForm.get('llmConfig.modelName')?.setValue(this.availableModels[0].value);
    }
  }

  onVectorStoreChange(type: string) {
    this.showConnectionString = type !== 'faiss';
    
    switch (type) {
      case 'qdrant':
        this.connectionStringPlaceholder = 'http://localhost:6333';
        break;
      case 'chroma':
        this.connectionStringPlaceholder = 'http://localhost:8000';
        break;
      default:
        this.connectionStringPlaceholder = '';
    }
  }

  loadConfiguration() {
    // Aquí cargarías la configuración desde el backend
    console.log('Loading configuration...');
  }

  saveConfiguration() {
    if (this.configForm.valid) {
      this.loading = true;
      const config: Configuration = this.configForm.value;
      
      // Simular guardado
      setTimeout(() => {
        this.loading = false;
        this.snackBar.open('Configuración guardada exitosamente', 'Cerrar', {
          duration: 3000,
          panelClass: ['success-snackbar']
        });
      }, 2000);
      
      console.log('Saving configuration:', config);
    }
  }

  testConfiguration() {
    this.loading = true;
    this.connectionStatus = [
      { service: 'Repositorio Origen', status: 'testing', message: 'Probando conexión...' },
      { service: 'Repositorio Destino', status: 'testing', message: 'Probando conexión...' },
      { service: 'LLM Provider', status: 'testing', message: 'Probando API...' },
      { service: 'Vector Store', status: 'testing', message: 'Probando conexión...' }
    ];

    // Simular prueba de conexiones
    setTimeout(() => {
      this.connectionStatus = [
        { service: 'Repositorio Origen', status: 'success', message: 'Conexión exitosa - 245 archivos encontrados' },
        { service: 'Repositorio Destino', status: 'success', message: 'Conexión exitosa - Permisos de escritura confirmados' },
        { service: 'LLM Provider', status: 'success', message: 'API funcional - Modelo disponible' },
        { service: 'Vector Store', status: 'error', message: 'Error de conexión - Verificar URL' }
      ];
      this.loading = false;
    }, 3000);
  }
}