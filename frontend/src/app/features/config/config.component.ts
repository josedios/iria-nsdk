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

  availableModels: { label: string, value: string }[] = [
    { label: 'GPT-5', value: 'gpt-5' },
    { label: 'GPT-4', value: 'gpt-4' },
    { label: 'GPT-4 Turbo', value: 'gpt-4-turbo-preview' },
    { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
  ];
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
    console.log('ConfigComponent ngOnInit - availableModels:', this.availableModels);
    this.loadConfigurations();
    // Inicializar modelos por defecto para OpenAI
    this.onProviderChange('openai');
    console.log('After onProviderChange - availableModels:', this.availableModels);
  }

  createForm(): FormGroup {
    return this.fb.group({
      name: ['', Validators.required],         // ✅ Solo el nombre es obligatorio
      description: [''],
      isActive: [true],
      sourceRepo: this.fb.group({
        url: [''],                             // ❌ Opcional - puede configurarse después
        branch: ['main'],
        username: [''],
        token: ['']
      }),
      frontendRepo: this.fb.group({
        url: [''],                             // ❌ Opcional - puede configurarse después
        branch: ['main'],
        username: [''],
        token: ['']
      }),
      backendRepo: this.fb.group({
        url: [''],                             // ❌ Opcional - puede configurarse después
        branch: ['main'],
        username: [''],
        token: ['']
      }),
      llmConfig: this.fb.group({
        provider: ['openai'],                  // ❌ Opcional - puede configurarse después
        apiKey: [''],
        baseUrl: [''],
        modelName: ['gpt-5'],
        temperature: [0.7, [Validators.min(0), Validators.max(2)]],
        maxTokens: [16384, [Validators.min(1), Validators.max(32768)]]
      }),
      vectorStoreConfig: this.fb.group({
        type: ['faiss'],                       // ❌ Opcional - puede configurarse después
        connectionString: [''],
        collectionName: ['nsdk-embeddings'],
        embeddingModel: ['text-embedding-ada-002'],
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
    // Validación mínima: solo requiere el nombre
    if (this.isFormValidForSaving()) {
      this.loading = true;
      const formValue = this.configForm.value;

      // Limpiar campos vacíos antes de guardar
      const cleanConfigData = this.cleanEmptyFields(formValue);

      const config: Configuration = {
        id: this.selectedConfigId || undefined,
        name: formValue.name,
        description: formValue.description || '',
        config_data: cleanConfigData
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
    console.log('Provider changed to:', provider);
    this.showApiKey = provider !== 'ollama';
    this.showBaseUrl = provider === 'ollama';

    switch (provider) {
      case 'openai':
        this.availableModels = [
          { label: 'GPT-5', value: 'gpt-5' },
          { label: 'GPT-4', value: 'gpt-4' },
          { label: 'GPT-4 Turbo', value: 'gpt-4-turbo-preview' },
          { label: 'GPT-3.5 Turbo', value: 'gpt-3.5-turbo' }
        ];
        console.log('Available models for OpenAI:', this.availableModels);
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

  /**
 * Validación mínima: solo requiere el nombre de la configuración
 * El usuario puede guardar en cualquier momento con cualquier campo
 */
  isFormValidForSaving(): boolean {
    const formValue = this.configForm.value;

    // Solo el nombre es obligatorio
    const hasName = formValue.name && formValue.name.trim() !== '';

    return hasName;
  }

  /**
   * Limpia campos vacíos para no guardar datos innecesarios
   * Solo guarda campos que tengan valor real
   */
  private cleanEmptyFields(formValue: any): any {
    const cleanData: any = {};

    // Solo incluir campos que tengan valor
    if (formValue.isActive !== undefined) {
      cleanData.isActive = formValue.isActive;
    }

    // Limpiar sourceRepo
    if (this.hasValidData(formValue.sourceRepo)) {
      cleanData.sourceRepo = this.cleanRepoData(formValue.sourceRepo);
    }

    // Limpiar frontendRepo
    if (this.hasValidData(formValue.frontendRepo)) {
      cleanData.frontendRepo = this.cleanRepoData(formValue.frontendRepo);
    }

    // Limpiar backendRepo
    if (this.hasValidData(formValue.backendRepo)) {
      cleanData.backendRepo = this.cleanRepoData(formValue.backendRepo);
    }

    // Limpiar llmConfig
    if (this.hasValidData(formValue.llmConfig)) {
      cleanData.llmConfig = this.cleanLLMData(formValue.llmConfig);
    }

    // Limpiar vectorStoreConfig
    if (this.hasValidData(formValue.vectorStoreConfig)) {
      cleanData.vectorStoreConfig = this.cleanVectorStoreData(formValue.vectorStoreConfig);
    }

    return cleanData;
  }

  /**
   * Verifica si un grupo de campos tiene datos válidos
   */
  private hasValidData(group: any): boolean {
    if (!group) return false;
    return Object.values(group).some(value =>
      value !== null && value !== undefined && value !== '' && value !== false
    );
  }

  /**
   * Limpia datos de repositorio
   */
  private cleanRepoData(repo: any): any {
    const cleanRepo: any = {};
    if (repo.url?.trim()) cleanRepo.url = repo.url.trim();
    if (repo.branch?.trim()) cleanRepo.branch = repo.branch.trim();
    if (repo.username?.trim()) cleanRepo.username = repo.username.trim();
    if (repo.token?.trim()) cleanRepo.token = repo.token.trim();
    return cleanRepo;
  }

  /**
   * Limpia datos de LLM
   */
  private cleanLLMData(llm: any): any {
    const cleanLLM: any = {};
    if (llm.provider?.trim()) cleanLLM.provider = llm.provider.trim();
    if (llm.apiKey?.trim()) cleanLLM.apiKey = llm.apiKey.trim();
    if (llm.baseUrl?.trim()) cleanLLM.baseUrl = llm.baseUrl.trim();
    if (llm.modelName?.trim()) cleanLLM.modelName = llm.modelName.trim();
    if (llm.temperature !== undefined) cleanLLM.temperature = llm.temperature;
    if (llm.maxTokens !== undefined) cleanLLM.maxTokens = llm.maxTokens;
    return cleanLLM;
  }

  /**
   * Limpia datos de Vector Store
   */
  private cleanVectorStoreData(vectorStore: any): any {
    const cleanVectorStore: any = {};
    if (vectorStore.type?.trim()) cleanVectorStore.type = vectorStore.type.trim();
    if (vectorStore.connectionString?.trim()) cleanVectorStore.connectionString = vectorStore.connectionString.trim();
    if (vectorStore.collectionName?.trim()) cleanVectorStore.collectionName = vectorStore.collectionName.trim();
    if (vectorStore.embeddingModel?.trim()) cleanVectorStore.embeddingModel = vectorStore.embeddingModel.trim();
    if (vectorStore.dimension !== undefined) cleanVectorStore.dimension = vectorStore.dimension;
    return cleanVectorStore;
  }
}