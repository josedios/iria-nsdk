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
  frontendRepo: RepositoryConfig;
  backendRepo: RepositoryConfig;
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
  templateUrl: './config.component.html',
  styleUrls: ['./config.component.scss']
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
  }

  createForm(): FormGroup {
    return this.fb.group({
      name: ['', Validators.required],
      isActive: [true],
      sourceRepo: this.fb.group({
        url: ['', Validators.required],
        branch: ['main', Validators.required],
        username: [''],
        token: ['']
      }),
      frontendRepo: this.fb.group({
        url: ['', Validators.required],
        branch: ['main', Validators.required],
        username: [''],
        token: ['']
      }),
      backendRepo: this.fb.group({
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
        temperature: [0.7, [Validators.min(0), Validators.max(2)]],
        maxTokens: [4096, [Validators.min(1), Validators.max(8192)]]
      }),
      vectorStoreConfig: this.fb.group({
        type: ['faiss', Validators.required],
        connectionString: [''],
        collectionName: ['nsdk-embeddings', Validators.required],
        embeddingModel: ['text-embedding-ada-002', Validators.required],
        dimension: [1536, [Validators.min(128), Validators.max(4096)]]
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
      { service: 'Repositorio Origen (NSDK)', status: 'testing', message: 'Probando conexión...' },
      { service: 'Repositorio Frontend (Angular)', status: 'testing', message: 'Probando conexión...' },
      { service: 'Repositorio Backend (Spring Boot)', status: 'testing', message: 'Probando conexión...' },
      { service: 'LLM Provider', status: 'testing', message: 'Probando API...' },
      { service: 'Vector Store', status: 'testing', message: 'Probando conexión...' }
    ];

    // Simular prueba de conexiones
    setTimeout(() => {
      this.connectionStatus = [
        { service: 'Repositorio Origen (NSDK)', status: 'success', message: 'Conexión exitosa - 245 archivos .SCR encontrados' },
        { service: 'Repositorio Frontend (Angular)', status: 'success', message: 'Conexión exitosa - Permisos de escritura confirmados' },
        { service: 'Repositorio Backend (Spring Boot)', status: 'success', message: 'Conexión exitosa - Permisos de escritura confirmados' },
        { service: 'LLM Provider', status: 'success', message: 'API funcional - Modelo GPT-4 disponible' },
        { service: 'Vector Store', status: 'error', message: 'Error de conexión - Verificar URL del servidor' }
      ];
      this.loading = false;
    }, 3000);
  }
}