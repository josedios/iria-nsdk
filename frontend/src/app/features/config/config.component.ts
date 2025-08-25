import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatTabsModule } from '@angular/material/tabs';
import { ConfigService, Configuration } from './config.service';

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
  configs: Configuration[] = [];
  selectedConfigId: string | null = null;

  availableModels: { label: string, value: string }[] = [];
  showApiKey = true;
  showBaseUrl = false;
  apiKeyPlaceholder = 'sk-...';

  showConnectionString = false;
  connectionStringPlaceholder = '';

  connectionStatus: { service: string, status: 'success' | 'error' | 'testing', message: string }[] | null = null;

  constructor(
    private fb: FormBuilder,
    private snackBar: MatSnackBar,
    private configService: ConfigService
  ) {
    this.configForm = this.createForm();
  }

  ngOnInit() {
    this.loadConfigurations();
  }

  createForm(): FormGroup {
    return this.fb.group({
      name: ['', Validators.required],
      description: [''],
      isActive: [true], // Añadir el campo isActive al formulario
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

  loadConfigurations() {
    this.loading = true;
    this.configService.getAll().subscribe({
      next: (configs) => {
        this.configs = configs;
        if (configs.length > 0) {
          this.selectConfiguration(configs[0]);
        }
        this.loading = false;
      },
      error: () => {
        this.snackBar.open('Error al cargar configuraciones', 'Cerrar', { duration: 3000, panelClass: ['error-snackbar'] });
        this.loading = false;
      }
    });
  }

  selectConfiguration(config: Configuration) {
    this.selectedConfigId = config.id || null;
    this.configForm.patchValue({
      name: config.name,
      description: config.description || '',
      isActive: config.config_data?.isActive ?? true, // Mapear isActive al cargar
      ...config.config_data
    });
  }

  saveConfiguration() {
    if (this.configForm.valid) {
      this.loading = true;
      const formValue = this.configForm.value;
      // Empaquetar todos los datos anidados en config_data
      const config: Configuration = {
        id: this.selectedConfigId || undefined,
        name: formValue.name,
        description: formValue.description,
        config_data: {
          isActive: formValue.isActive, // Guardar isActive
          sourceRepo: formValue.sourceRepo,
          frontendRepo: formValue.frontendRepo,
          backendRepo: formValue.backendRepo,
          llmConfig: formValue.llmConfig,
          vectorStoreConfig: formValue.vectorStoreConfig
        }
      };
      let obs;
      if (this.selectedConfigId) {
        obs = this.configService.update(this.selectedConfigId, config);
      } else {
        obs = this.configService.create(config);
      }
      obs.subscribe({
        next: () => {
          this.snackBar.open('Configuración guardada exitosamente', 'Cerrar', { duration: 3000, panelClass: ['success-snackbar'] });
          this.loading = false;
        },
        error: () => {
          this.snackBar.open('Error al guardar configuración', 'Cerrar', { duration: 3000, panelClass: ['error-snackbar'] });
          this.loading = false;
        }
      });
    }
  }

  deleteConfiguration() {
    if (this.selectedConfigId) {
      this.loading = true;
      this.configService.delete(this.selectedConfigId).subscribe({
        next: () => {
          this.snackBar.open('Configuración eliminada', 'Cerrar', { duration: 3000, panelClass: ['success-snackbar'] });
          this.selectedConfigId = null;
          this.configForm.reset();
          this.loadConfigurations();
          this.loading = false;
        },
        error: () => {
          this.snackBar.open('Error al eliminar configuración', 'Cerrar', { duration: 3000, panelClass: ['error-snackbar'] });
          this.loading = false;
        }
      });
    }
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

  testConfiguration() {
    this.loading = true;
    const formValue = this.configForm.value;
    const config_data = {
      isActive: formValue.isActive,
      sourceRepo: formValue.sourceRepo,
      frontendRepo: formValue.frontendRepo,
      backendRepo: formValue.backendRepo,
      llmConfig: formValue.llmConfig,
      vectorStoreConfig: formValue.vectorStoreConfig
    };
    this.configService.testConnections(config_data).subscribe({
      next: (results) => {
        this.connectionStatus = results;
        this.loading = false;
      },
      error: () => {
        this.snackBar.open('Error al probar conexiones', 'Cerrar', { duration: 3000, panelClass: ['error-snackbar'] });
        this.loading = false;
      }
    });
  }
}