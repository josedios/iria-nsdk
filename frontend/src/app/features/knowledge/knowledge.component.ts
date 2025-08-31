import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDialog, MatDialogModule } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSortModule } from '@angular/material/sort';
import { MatTableModule } from '@angular/material/table';
import { MatTabsModule } from '@angular/material/tabs';
import { ConfigService, Configuration } from '../config/config.service';
import { KnowledgeService, SearchCodeRequest, VectorizationBatch, VectorizationStats, VectorizeRepositoryRequest } from './knowledge.service';

// Interfaces locales para el componente
interface LocalVectorizationStats {
  totalDocuments: number;
  sourceDocuments: number;
  targetDocuments: number;
  backendDocuments: number;
  documentationDocuments: number;
  lastUpdated: string;
  collectionSize: string;
}

interface DocumentInfo {
  id: string;
  name: string;
  type: 'nsdk_source' | 'target_code' | 'documentation';
  size: string;
  lastModified: string;
  status: 'indexed' | 'pending' | 'error';
  similarity?: number;
}

// Interfaz local para resultados de búsqueda (compatible con el template)
interface LocalSearchResult {
  id: string;
  content: string;
  metadata: {
    source: string;
    file_path: string;
    file_type: string;
  };
  similarity: number;
}

@Component({
  selector: 'app-knowledge',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTabsModule,
    MatChipsModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatTableModule,
    MatPaginatorModule,
    MatSortModule,
    MatSnackBarModule,
    MatDialogModule,
    MatProgressSpinnerModule
  ],
  templateUrl: './knowledge.component.html',
  styleUrls: ['./knowledge.component.scss']
})
export class KnowledgeComponent implements OnInit {
  // Estados
  isVectorizing = false;
  isSearching = false;
  isLoadingDocuments = false;

  // Estado de configuración
  hasConfiguration = false;
  hasSourceRepo = false;
  hasFrontendRepo = false;
  hasBackendRepo = false;

  // Datos de estadísticas
  stats: LocalVectorizationStats = {
    totalDocuments: 0,
    sourceDocuments: 0,
    targetDocuments: 0,
    backendDocuments: 0,
    documentationDocuments: 0,
    lastUpdated: 'Nunca',
    collectionSize: '0 archivos'
  };

  // Estado de vectorización
  vectorizationStatus = '';

  // Progreso por repositorio
  repositoryProgress: { [key: string]: { processed: number; total: number; progress: number } } = {};

  // Búsqueda
  searchQuery = '';
  searchType = 'all';
  searchResults: LocalSearchResult[] = [];

  // Documentos
  documents: DocumentInfo[] = [];
  displayedColumns = ['name', 'type', 'size', 'status', 'lastModified', 'actions'];

  constructor(
    private snackBar: MatSnackBar,
    private dialog: MatDialog,
    private knowledgeService: KnowledgeService,
    private configService: ConfigService
  ) { }

  ngOnInit() {
    // Primero cargar configuración, luego estadísticas y documentos
    this.loadConfiguration();
  }

  private loadConfiguration() {
    this.configService.getAll().subscribe({
      next: (configurations: Configuration[]) => {
        if (configurations.length > 0) {
          const activeConfig = configurations[0];
          this.updateConfigurationStatus(activeConfig.config_data);
        }

        // Continuar con la carga de estadísticas
        this.loadVectorizationStats();
      },
      error: (error) => {
        console.error('Error cargando configuración:', error);
        // Continuar sin configuración
        this.loadVectorizationStats();
      }
    });
  }

  private updateConfigurationStatus(configData: any) {
    this.hasConfiguration = true;
    this.hasSourceRepo = !!(configData.sourceRepo?.url && configData.sourceRepo?.branch);
    this.hasFrontendRepo = !!(configData.frontendRepo?.url && configData.frontendRepo?.branch);
    this.hasBackendRepo = !!(configData.backendRepo?.url && configData.backendRepo?.branch);

    console.log('Estado de configuración actualizado:', {
      hasSourceRepo: this.hasSourceRepo,
      hasFrontendRepo: this.hasFrontendRepo,
      hasBackendRepo: this.hasBackendRepo,
      sourceRepoUrl: configData.sourceRepo?.url,
      sourceRepoBranch: configData.sourceRepo?.branch
    });
  }

  vectorizeRepositories() {
    // Verificar si ya está vectorizando
    if (!this.canStartVectorization()) {
      this.snackBar.open('Vectorización ya en progreso. Espera a que termine.', 'Cerrar', {
        duration: 3000,
        panelClass: ['warning-snackbar']
      });
      return;
    }

    console.log('Iniciando vectorización de todos los repositorios...');

    // Limpiar estado anterior si existe
    this.clearVectorizationState();

    // Obtener la configuración activa del sistema
    this.loadActiveConfigurationAndVectorize();
  }

  private loadActiveConfigurationAndVectorize() {
    // Obtener configuración activa del sistema
    this.configService.getAll().subscribe({
      next: (configurations: Configuration[]) => {
        if (configurations.length === 0) {
          this.snackBar.open('No hay configuraciones disponibles. Configure los repositorios primero.', 'Cerrar', {
            duration: 5000,
            panelClass: ['error-snackbar']
          });
          return;
        }

        // Usar la primera configuración activa (podríamos implementar lógica para seleccionar la activa)
        const activeConfig = configurations[0];
        console.log('Configuración activa encontrada:', activeConfig);

        // Verificar qué repositorios están configurados y vectorizar solo los que faltan
        this.analyzeAndVectorizeRepositories(activeConfig.config_data);
      },
      error: (error) => {
        console.error('Error obteniendo configuraciones:', error);
        this.snackBar.open('Error obteniendo configuración: ' + error.message, 'Cerrar', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }

  private analyzeAndVectorizeRepositories(configData: any) {
    // Analizar qué repositorios están configurados
    const configuredRepos = this.getConfiguredRepositories(configData);

    console.log('DEBUG: analyzeAndVectorizeRepositories - configData recibido:', configData);
    console.log('DEBUG: analyzeAndVectorizeRepositories - configuredRepos resultante:', configuredRepos);

    if (Object.keys(configuredRepos).length === 0) {
      this.snackBar.open('No hay repositorios configurados. Configure al menos el repositorio NSDK.', 'Cerrar', {
        duration: 5000,
        panelClass: ['error-snackbar']
      });
      return;
    }

    console.log('Repositorios configurados:', configuredRepos);

    // Verificar qué repositorios ya están vectorizados
    this.checkVectorizationStatus(configuredRepos);
  }

  private getConfiguredRepositories(configData: any): any {
    console.log('DEBUG: getConfiguredRepositories - configData recibido:', configData);

    const repos: any = {};

    // Verificar repositorio NSDK (origen) - obligatorio
    if (configData.sourceRepo?.url && configData.sourceRepo?.branch) {
      repos.sourceRepo = {
        url: configData.sourceRepo.url,
        branch: configData.sourceRepo.branch,
        username: configData.sourceRepo.username,
        token: configData.sourceRepo.token
      };
      console.log('DEBUG: sourceRepo configurado:', repos.sourceRepo);
    } else {
      console.log('DEBUG: sourceRepo NO configurado - url:', configData.sourceRepo?.url, 'branch:', configData.sourceRepo?.branch);
    }

    // Verificar repositorio Frontend - opcional
    if (configData.frontendRepo?.url && configData.frontendRepo?.branch) {
      repos.frontendRepo = {
        url: configData.frontendRepo.url,
        branch: configData.frontendRepo.branch,
        username: configData.frontendRepo.username,
        token: configData.frontendRepo.token
      };
      console.log('DEBUG: frontendRepo configurado:', repos.frontendRepo);
    } else {
      console.log('DEBUG: frontendRepo NO configurado - url:', configData.frontendRepo?.url, 'branch:', configData.frontendRepo?.branch);
    }

    // Verificar repositorio Backend - opcional
    if (configData.backendRepo?.url && configData.backendRepo?.branch) {
      repos.backendRepo = {
        url: configData.backendRepo.url,
        branch: configData.backendRepo.branch,
        username: configData.backendRepo.username,
        token: configData.backendRepo.token
      };
      console.log('DEBUG: backendRepo configurado:', repos.backendRepo);
    } else {
      console.log('DEBUG: backendRepo NO configurado - url:', configData.backendRepo?.url, 'branch:', configData.backendRepo?.branch);
    }

    console.log('DEBUG: getConfiguredRepositories - repos final:', repos);
    return repos;
  }

  private checkVectorizationStatus(configuredRepos: any) {
    // Verificar estado de vectorización de cada repositorio
    // Por ahora, asumimos que no están vectorizados y procedemos
    // En el futuro, aquí podríamos verificar en la BD qué repositorios ya están vectorizados

    this.startSmartVectorization(configuredRepos);
  }

  private startSmartVectorization(configuredRepos: any) {
    // Verificar si ya está vectorizando
    if (this.isVectorizing) {
      console.warn('Vectorización ya en progreso, ignorando nueva solicitud');
      return;
    }

    console.log('DEBUG: startSmartVectorization - configuredRepos recibido:', configuredRepos);
    console.log('DEBUG: startSmartVectorization - typeof configuredRepos:', typeof configuredRepos);
    console.log('DEBUG: startSmartVectorization - Object.keys(configuredRepos):', Object.keys(configuredRepos));

    this.isVectorizing = true;
    this.vectorizationStatus = '🔄 Actualizando repositorios y limpiando vectorización existente...';

    // Inicializar progreso por repositorio
    this.repositoryProgress = {};
    console.log('DEBUG: repositoryProgress inicializado como objeto vacío:', this.repositoryProgress);

    if (configuredRepos.sourceRepo) {
      this.repositoryProgress['nsdk_source'] = { processed: 0, total: 0, progress: 0 };
      console.log('DEBUG: Progreso inicializado para nsdk_source:', this.repositoryProgress['nsdk_source']);
    } else {
      console.log('DEBUG: NO se inicializó progreso para nsdk_source porque configuredRepos.sourceRepo es falsy');
    }

    if (configuredRepos.frontendRepo) {
      this.repositoryProgress['frontend_code'] = { processed: 0, total: 0, progress: 0 };
      console.log('DEBUG: Progreso inicializado para frontend_code:', this.repositoryProgress['frontend_code']);
    } else {
      console.log('DEBUG: NO se inicializó progreso para frontend_code porque configuredRepos.frontendRepo es falsy');
    }

    if (configuredRepos.backendRepo) {
      this.repositoryProgress['backend_code'] = { processed: 0, total: 0, progress: 0 };
      console.log('DEBUG: Progreso inicializado para backend_code:', this.repositoryProgress['backend_code']);
    } else {
      console.log('DEBUG: NO se inicializó progreso para backend_code porque configuredRepos.backendRepo es falsy');
    }

    console.log('DEBUG: Estado final de repositoryProgress después de inicialización:', this.repositoryProgress);

    // Crear array de promesas solo para repositorios configurados
    const vectorizationPromises: Promise<any>[] = [];

    // NSDK siempre se vectoriza (es obligatorio)
    if (configuredRepos.sourceRepo) {
      console.log('DEBUG: Añadiendo promesa para nsdk_source');
      vectorizationPromises.push(
        this.vectorizeSingleRepository(configuredRepos.sourceRepo, 'NSDK (Origen)', 'nsdk_source')
      );
    } else {
      console.log('DEBUG: NO se añadió promesa para nsdk_source porque configuredRepos.sourceRepo es falsy');
    }

    // Frontend solo si está configurado
    if (configuredRepos.frontendRepo) {
      console.log('DEBUG: Añadiendo promesa para frontend_code');
      vectorizationPromises.push(
        this.vectorizeSingleRepository(configuredRepos.frontendRepo, 'Frontend Angular', 'frontend_code')
      );
    } else {
      console.log('DEBUG: NO se añadió promesa para frontend_code porque configuredRepos.frontendRepo es falsy');
    }

    // Backend solo si está configurado
    if (configuredRepos.backendRepo) {
      console.log('DEBUG: Añadiendo promesa para backend_code');
      vectorizationPromises.push(
        this.vectorizeSingleRepository(configuredRepos.backendRepo, 'Backend Spring Boot', 'backend_code')
      );
    } else {
      console.log('DEBUG: NO se añadió promesa para backend_code porque configuredRepos.backendRepo es falsy');
    }

    console.log('DEBUG: Total de promesas creadas:', vectorizationPromises.length);

    if (vectorizationPromises.length === 0) {
      console.log('DEBUG: No hay promesas para vectorizar, limpiando estado');
      this.isVectorizing = false;
      this.vectorizationStatus = 'No hay repositorios para vectorizar';
      return;
    }

    // Vectorizar solo los repositorios configurados
    Promise.all(vectorizationPromises)
      .then((results) => {
        console.log('Vectorización inteligente completada:', results);
        this.vectorizationStatus = '✅ Vectorización completada exitosamente';

        // Mantener la interfaz visible por más tiempo para mostrar el progreso final
        setTimeout(() => {
          this.isVectorizing = false;
          console.log('Interfaz de progreso ocultada después de completar');
        }, 5000); // 5 segundos para ver el resultado final

        this.snackBar.open(`Vectorización completada para ${vectorizationPromises.length} repositorio(s)`, 'Cerrar', {
          duration: 5000,
          panelClass: ['success-snackbar']
        });

        // Refrescar estadísticas
        this.refreshAllData();
      })
      .catch((error) => {
        console.error('Error en vectorización inteligente:', error);
        this.vectorizationStatus = '❌ Error en vectorización';

        // Mantener la interfaz visible para mostrar el error
        setTimeout(() => {
          this.isVectorizing = false;
          console.log('Interfaz de progreso ocultada después del error');
        }, 3000);

        this.snackBar.open('Error en vectorización: ' + error.message, 'Cerrar', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      });
  }

  // Método anterior eliminado - reemplazado por startSmartVectorization

  private vectorizeSingleRepository(repoConfig: any, repoName: string, repoType: string): Promise<any> {
    return new Promise((resolve, reject) => {
      // Obtener la configuración activa para obtener el config_id
      this.configService.getAll().subscribe({
        next: (configurations: Configuration[]) => {
          if (configurations.length === 0) {
            reject(new Error('No hay configuraciones disponibles'));
            return;
          }

          const activeConfig = configurations[0];

          // Mapear el tipo de repositorio al tipo esperado por el backend
          let backendRepoType: string;
          switch (repoType) {
            case 'nsdk_source':
              backendRepoType = 'source';
              break;
            case 'frontend_code':
              backendRepoType = 'frontend';
              break;
            case 'backend_code':
              backendRepoType = 'backend';
              break;
            default:
              backendRepoType = 'source';
          }

          const vectorizeRequest: VectorizeRepositoryRequest = {
            config_id: activeConfig.id!,
            repo_type: backendRepoType,
            branch: repoConfig.branch
          };

          this.knowledgeService.vectorizeRepository(vectorizeRequest).subscribe({
            next: (response) => {
              console.log(`Vectorización iniciada para ${repoName}:`, response);

              // Monitorear progreso específico de este repositorio
              if (response.batch_id) {
                this.monitorRepositoryProgress(response.batch_id, repoName, repoType, resolve, reject);
              } else {
                resolve(response);
              }
            },
            error: (error) => {
              console.error(`Error vectorizando ${repoName}:`, error);
              reject(error);
            }
          });
        },
        error: (error) => {
          console.error('Error obteniendo configuraciones:', error);
          reject(new Error('Error obteniendo configuración'));
        }
      });
    });
  }

  private monitorRepositoryProgress(batchId: string, repoName: string, repoType: string, resolve: Function, reject: Function) {
    console.log(`DEBUG: monitorRepositoryProgress iniciado para ${repoName} (${repoType})`);
    console.log(`DEBUG: repositoryProgress al inicio de monitorRepositoryProgress:`, this.repositoryProgress);
    console.log(`DEBUG: ¿Existe repositoryProgress[${repoType}]?:`, this.repositoryProgress[repoType] !== undefined);

    const checkProgress = () => {
      console.log(`DEBUG: checkProgress ejecutándose para ${repoName} (${repoType})`);
      console.log(`DEBUG: repositoryProgress antes de getBatchStatus:`, this.repositoryProgress);

      this.knowledgeService.getBatchStatus(batchId).subscribe({
        next: (batch: VectorizationBatch) => {
          console.log(`DEBUG: Progreso recibido para ${repoName} (${repoType}):`, batch);
          console.log(`DEBUG: repositoryProgress antes de updateOverallProgress:`, this.repositoryProgress);

          // Actualizar progreso del repositorio específico
          this.updateOverallProgress(batch, repoType);

          console.log(`DEBUG: repositoryProgress después de updateOverallProgress:`, this.repositoryProgress);

          if (batch.status === 'in_progress') {
            // Mostrar progreso detallado
            const repoProgress = this.repositoryProgress[repoType];
            console.log(`DEBUG: repoProgress obtenido para ${repoType}:`, repoProgress);

            if (repoProgress) {
              this.vectorizationStatus = `📊 Vectorizando ${repoName}: ${repoProgress.processed}/${repoProgress.total} archivos (${repoProgress.progress}%)`;
              console.log(`DEBUG: Estado actualizado: ${this.vectorizationStatus}`);
            } else {
              console.log(`DEBUG: NO se encontró repoProgress para ${repoType}, usando estado genérico`);
              this.vectorizationStatus = `📊 Vectorizando ${repoName}...`;
            }

            // Continuar monitoreando con intervalo más corto para mejor UX
            setTimeout(() => checkProgress(), 1000);
          } else if (batch.status === 'completed') {
            console.log(`DEBUG: ${repoName} (${repoType}) completado exitosamente`);
            this.vectorizationStatus = `${repoName} vectorizado exitosamente`;

            // Mantener la interfaz visible por un momento antes de resolver
            setTimeout(() => {
              resolve(batch);
            }, 2000);
          } else if (batch.status === 'failed') {
            console.error(`DEBUG: Vectorización fallida para ${repoName} (${repoType})`);
            reject(new Error(`Vectorización fallida para ${repoName}`));
          }
        },
        error: (error) => {
          console.error(`DEBUG: Error obteniendo progreso de ${repoName} (${repoType}):`, error);
          reject(error);
        }
      });
    };

    checkProgress();
  }

  private updateOverallProgress(batch: VectorizationBatch, repoType: string) {
    console.log(`DEBUG: updateOverallProgress llamado para ${repoType}`);
    console.log(`DEBUG: batch recibido:`, batch);
    console.log(`DEBUG: repositoryProgress actual:`, this.repositoryProgress);
    console.log(`DEBUG: Object.keys(repositoryProgress):`, Object.keys(this.repositoryProgress));
    console.log(`DEBUG: ¿Existe repositoryProgress[${repoType}]?:`, this.repositoryProgress[repoType] !== undefined);

    console.log(`Actualizando progreso para ${repoType}:`, {
      processed: batch.processed_files,
      total: batch.total_files,
      status: batch.status
    });

    // Actualizar progreso del repositorio específico
    if (this.repositoryProgress[repoType]) {
      this.repositoryProgress[repoType].processed = batch.processed_files || 0;
      this.repositoryProgress[repoType].total = batch.total_files || 0;
      this.repositoryProgress[repoType].progress = batch.total_files > 0 ?
        Math.round((batch.processed_files / batch.total_files) * 100) : 0;

      console.log(`DEBUG: Progreso actualizado para ${repoType}:`, this.repositoryProgress[repoType]);
    } else {
      console.error(`ERROR: No se encontró progreso para ${repoType} en repositoryProgress:`, this.repositoryProgress);
      console.error(`ERROR: repoType: ${repoType}, typeof: ${typeof repoType}`);
      console.error(`ERROR: repositoryProgress keys:`, Object.keys(this.repositoryProgress));
    }

    // Forzar detección de cambios para Angular
    this.vectorizationStatus = this.vectorizationStatus; // Trigger change detection
  }



  private showVectorizationSuccess(repoType: string) {
    // Aquí podrías implementar lógica para mostrar indicadores visuales de éxito
    // Por ejemplo, cambiar el color del botón, mostrar un checkmark, etc.
    console.log(`Vectorización exitosa para ${repoType}`);

    // Opcional: Actualizar estadísticas específicas del repositorio
    setTimeout(() => {
      this.loadVectorizationStats();
    }, 1000);
  }

  // Método para obtener progreso detallado por repositorio
  getRepositoryProgress(repoType: string): { processed: number; total: number; progress: number } | null {
    return this.repositoryProgress[repoType] || null;
  }

  // Método para verificar si un repositorio está siendo vectorizado
  isRepositoryVectorizing(repoType: string): boolean {
    return this.isVectorizing && this.repositoryProgress[repoType] !== undefined;
  }

  // Método para limpiar estado de vectorización
  private clearVectorizationState() {
    this.isVectorizing = false;
    this.vectorizationStatus = '';
    this.repositoryProgress = {};
    console.log('Estado de vectorización limpiado');
  }

  // Método para verificar si se puede iniciar nueva vectorización
  canStartVectorization(): boolean {
    return !this.isVectorizing;
  }

  // Método para vectorizar un repositorio específico (para uso futuro)
  vectorizeSpecificRepository(repoType: 'nsdk_source' | 'frontend_code' | 'backend_code') {
    this.configService.getAll().subscribe({
      next: (configurations: Configuration[]) => {
        if (configurations.length === 0) {
          this.snackBar.open('No hay configuraciones disponibles.', 'Cerrar', {
            duration: 5000,
            panelClass: ['error-snackbar']
          });
          return;
        }

        const activeConfig = configurations[0];
        const configData = activeConfig.config_data;
        let repoConfig: any = null;
        let repoName = '';

        // Obtener configuración del repositorio específico
        switch (repoType) {
          case 'nsdk_source':
            if (configData.sourceRepo?.url && configData.sourceRepo?.branch) {
              repoConfig = {
                url: configData.sourceRepo.url,
                branch: configData.sourceRepo.branch,
                username: configData.sourceRepo.username,
                token: configData.sourceRepo.token
              };
              repoName = 'NSDK (Origen)';
            }
            break;
          case 'frontend_code':
            if (configData.frontendRepo?.url && configData.frontendRepo?.branch) {
              repoConfig = {
                url: configData.frontendRepo.url,
                branch: configData.frontendRepo.branch,
                username: configData.frontendRepo.username,
                token: configData.frontendRepo.token
              };
              repoName = 'Frontend Angular';
            }
            break;
          case 'backend_code':
            if (configData.backendRepo?.url && configData.backendRepo?.branch) {
              repoConfig = {
                url: configData.backendRepo.url,
                branch: configData.backendRepo.branch,
                username: configData.backendRepo.username,
                token: configData.backendRepo.token
              };
              repoName = 'Backend Spring Boot';
            }
            break;
        }

        if (!repoConfig) {
          this.snackBar.open(`El repositorio ${repoType} no está configurado.`, 'Cerrar', {
            duration: 5000,
            panelClass: ['error-snackbar']
          });
          return;
        }

        // Vectorizar solo este repositorio
        this.isVectorizing = true;
        this.vectorizationStatus = `Vectorizando ${repoName}...`;

        this.vectorizeSingleRepository(repoConfig, repoName, repoType)
          .then((result) => {
            this.isVectorizing = false;
            this.vectorizationStatus = `${repoName} vectorizado exitosamente`;
            this.snackBar.open(`${repoName} vectorizado exitosamente`, 'Cerrar', {
              duration: 3000,
              panelClass: ['success-snackbar']
            });

            // Actualizar estado y refrescar datos
            this.refreshAllData();

            // Mostrar indicador de éxito en el botón específico
            this.showVectorizationSuccess(repoType);
          })
          .catch((error) => {
            this.isVectorizing = false;
            this.vectorizationStatus = `Error vectorizando ${repoName}`;
            this.snackBar.open(`Error vectorizando ${repoName}: ${error.message}`, 'Cerrar', {
              duration: 5000,
              panelClass: ['error-snackbar']
            });
          });
      },
      error: (error) => {
        console.error('Error obteniendo configuraciones:', error);
        this.snackBar.open('Error obteniendo configuración: ' + error.message, 'Cerrar', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }

  // Método anterior eliminado - reemplazado por startMultiRepositoryVectorization

  private loadVectorizationStats() {
    this.knowledgeService.getVectorizationStats().subscribe({
      next: (stats: VectorizationStats) => {
        console.log('Estadísticas de vectorización:', stats);

        // Mapear estadísticas por tipo de repositorio
        if (stats.by_repository_type) {
          this.stats.sourceDocuments = stats.by_repository_type.nsdk?.total || 0;
          this.stats.targetDocuments = stats.by_repository_type.angular?.total || 0;
          this.stats.backendDocuments = stats.by_repository_type.spring_boot?.total || 0;
        } else {
          // Fallback a estadísticas agregadas si no hay separación por tipo
          this.stats.sourceDocuments = stats.vectorized_files || 0;
          this.stats.targetDocuments = 0;
          this.stats.backendDocuments = 0;
        }

        // Estadísticas agregadas
        this.stats.totalDocuments = stats.total_files || 0;
        this.stats.documentationDocuments = 0; // Por ahora
        this.stats.lastUpdated = stats.last_vectorization || 'Nunca';
        this.stats.collectionSize = `${stats.total_files || 0} archivos`;

        console.log('Estadísticas mapeadas:', this.stats);

        // Después de cargar estadísticas, cargar documentos
        this.loadDocuments();
      },
      error: (error) => {
        console.error('Error cargando estadísticas:', error);
        // Mantener estadísticas por defecto y cargar documentos
        this.loadDocuments();
      }
    });
  }



  performSearch() {
    if (!this.searchQuery) return;

    this.isSearching = true;
    this.searchResults = [];

    const searchRequest: SearchCodeRequest = {
      query: this.searchQuery,
      limit: 10
    };

    this.knowledgeService.searchSimilarCode(searchRequest).subscribe({
      next: (response) => {
        console.log('Resultados de búsqueda:', response);
        // Mapear resultados del backend a la interfaz local
        this.searchResults = response.results.map(result => ({
          id: result.id || '',
          content: result.metadata?.content || result.metadata?.file_path || 'Sin contenido',
          metadata: {
            source: result.metadata?.source || 'unknown',
            file_path: result.metadata?.file_path || '',
            file_type: result.metadata?.file_type || ''
          },
          similarity: result.score || 0
        })) as LocalSearchResult[];
        this.isSearching = false;

        if (this.searchResults.length === 0) {
          this.snackBar.open('No se encontraron resultados para tu búsqueda', 'Cerrar', {
            duration: 3000
          });
        }
      },
      error: (error) => {
        console.error('Error en búsqueda:', error);
        this.isSearching = false;
        this.snackBar.open('Error en búsqueda: ' + error.message, 'Cerrar', {
          duration: 5000,
          panelClass: ['error-snackbar']
        });
      }
    });
  }

  loadDocuments() {
    this.isLoadingDocuments = true;
    console.log('Cargando documentos del backend...');

    // TODO: Implementar endpoint real para obtener documentos
    // Por ahora, usar estadísticas para generar documentos simulados
    // pero en el futuro esto debería ser una llamada real al backend

    if (this.hasVectorizationData()) {
      // Si hay datos de vectorización, generar documentos basados en estadísticas reales
      setTimeout(() => {
        this.documents = this.generateSimulatedDocuments();
        this.isLoadingDocuments = false;
        console.log(`Documentos generados basados en estadísticas: ${this.documents.length}`);
      }, 500);
    } else {
      // Si no hay datos, mostrar documentos de ejemplo
      setTimeout(() => {
        this.documents = this.generateExampleDocuments();
        this.isLoadingDocuments = false;
        console.log('Documentos de ejemplo generados:', this.documents.length);
      }, 500);
    }
  }

  private generateSimulatedDocuments(): DocumentInfo[] {
    const documents: DocumentInfo[] = [];
    console.log('Generando documentos simulados con estadísticas:', this.stats);

    // Generar documentos NSDK basados en las estadísticas
    if (this.stats.sourceDocuments > 0) {
      const numDocs = Math.min(this.stats.sourceDocuments, 20); // Mostrar hasta 20 documentos
      console.log(`Generando ${numDocs} documentos NSDK`);

      for (let i = 1; i <= numDocs; i++) {
        documents.push({
          id: `nsdk_${i}`,
          name: `NSDK_File_${i}.SCR`,
          type: 'nsdk_source' as const,
          size: `${Math.floor(Math.random() * 10 + 1)}.${Math.floor(Math.random() * 9)} KB`,
          lastModified: new Date().toLocaleString(),
          status: 'indexed' as const
        });
      }
    }

    // Generar documentos de código moderno
    if (this.stats.targetDocuments > 0) {
      for (let i = 1; i <= Math.min(this.stats.targetDocuments, 5); i++) {
        documents.push({
          id: `target_${i}`,
          name: `Component_${i}.ts`,
          type: 'target_code' as const,
          size: `${Math.floor(Math.random() * 20 + 5)}.${Math.floor(Math.random() * 9)} KB`,
          lastModified: new Date().toLocaleString(),
          status: 'indexed' as const
        });
      }
    }

    // Generar documentos de documentación
    if (this.stats.documentationDocuments > 0) {
      for (let i = 1; i <= Math.min(this.stats.documentationDocuments, 3); i++) {
        documents.push({
          id: `doc_${i}`,
          name: `Documentation_${i}.pdf`,
          type: 'documentation' as const,
          size: `${Math.floor(Math.random() * 5 + 1)}.${Math.floor(Math.random() * 9)} MB`,
          lastModified: new Date().toLocaleString(),
          status: 'indexed' as const
        });
      }
    }

    return documents;
  }

  private generateExampleDocuments(): DocumentInfo[] {
    // Documentos de ejemplo para mostrar cuando no hay vectorización
    return [
      {
        id: '1',
        name: 'FACT001.SCR',
        type: 'nsdk_source' as const,
        size: '2.4 KB',
        lastModified: '2024-01-15 10:30',
        status: 'pending' as const
      },
      {
        id: '2',
        name: 'InvoiceComponent.ts',
        type: 'target_code' as const,
        size: '8.7 KB',
        lastModified: '2024-01-15 09:15',
        status: 'indexed' as const
      },
      {
        id: '3',
        name: 'business-rules.pdf',
        type: 'documentation' as const,
        size: '1.2 MB',
        lastModified: '2024-01-14 16:45',
        status: 'pending' as const
      }
    ];
  }

  private refreshAllData() {
    // Refresca todos los datos después de una vectorización
    // Primero cargar estadísticas, luego documentos cuando las estadísticas estén listas
    this.knowledgeService.getVectorizationStats().subscribe({
      next: (stats: VectorizationStats) => {
        console.log('Estadísticas actualizadas después de vectorización:', stats);
        // Mapear propiedades del backend a la interfaz local
        this.stats.totalDocuments = stats.total_files || 0;
        this.stats.sourceDocuments = stats.vectorized_files || 0;
        this.stats.targetDocuments = 0; // Por ahora
        this.stats.documentationDocuments = 0; // Por ahora
        this.stats.lastUpdated = stats.last_vectorization || 'Nunca';
        this.stats.collectionSize = `${stats.total_files || 0} archivos`;

        // Ahora cargar documentos con las estadísticas actualizadas
        this.loadDocuments();
        console.log('Documentos actualizados después de vectorización');
      },
      error: (error) => {
        console.error('Error cargando estadísticas después de vectorización:', error);
        // Intentar cargar documentos con estadísticas existentes
        this.loadDocuments();
      }
    });
  }

  // TODO: Implementar cuando el backend tenga endpoint para documentos
  private loadRealDocumentsFromBackend() {
    // Este método debería:
    // 1. Llamar a this.knowledgeService.getDocuments()
    // 2. Mapear la respuesta a DocumentInfo[]
    // 3. Actualizar this.documents
    // 4. Mantener persistencia real entre sesiones

    console.log('Método para cargar documentos reales del backend (a implementar)');

    // Ejemplo de implementación futura:
    /*
    this.knowledgeService.getDocuments().subscribe({
      next: (response) => {
        this.documents = response.documents.map(doc => ({
          id: doc.id,
          name: doc.name,
          type: doc.type,
          size: doc.size,
          lastModified: doc.last_modified,
          status: doc.status
        }));
        this.isLoadingDocuments = false;
      },
      error: (error) => {
        console.error('Error cargando documentos del backend:', error);
        this.isLoadingDocuments = false;
        // Fallback a documentos simulados
        this.documents = this.generateSimulatedDocuments();
      }
    });
    */
  }

  // Métodos auxiliares para el template
  trackByResultId(index: number, result: LocalSearchResult): string {
    return result.id;
  }

  getFileName(filePath: string): string {
    return filePath.split('/').pop() || filePath;
  }

  getSourceLabel(source: string): string {
    const labels = {
      'nsdk_source': 'NSDK Legacy',
      'frontend_code': 'Frontend Angular',
      'backend_code': 'Backend Spring Boot',
      'target_code': 'Código Moderno', // Mantener compatibilidad
      'documentation': 'Documentación'
    };
    return labels[source as keyof typeof labels] || source;
  }

  getDocumentIcon(type: string): string {
    const icons = {
      'nsdk_source': 'code',
      'frontend_code': 'web',
      'backend_code': 'settings',
      'target_code': 'web', // Mantener compatibilidad
      'documentation': 'description'
    };
    return icons[type as keyof typeof icons] || 'description';
  }

  getTypeLabel(type: string): string {
    return this.getSourceLabel(type);
  }

  getStatusLabel(status: string): string {
    const labels = {
      'indexed': 'Indexado',
      'pending': 'Pendiente',
      'error': 'Error'
    };
    return labels[status as keyof typeof labels] || status;
  }

  // Acciones
  copyToClipboard(content: string) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(content).then(() => {
        this.snackBar.open('Código copiado al portapapeles', 'Cerrar', { duration: 2000 });
      }).catch(() => {
        this.snackBar.open('Error al copiar al portapapeles', 'Cerrar', { duration: 2000 });
      });
    } else {
      // Fallback para navegadores que no soportan clipboard API
      const textArea = document.createElement('textarea');
      textArea.value = content;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      this.snackBar.open('Código copiado al portapapeles', 'Cerrar', { duration: 2000 });
    }
  }

  findSimilar(result: LocalSearchResult) {
    this.searchQuery = result.content.substring(0, 100) + '...';
    this.performSearch();
  }

  viewResultDetails(result: LocalSearchResult) {
    console.log('Viewing details for:', result);
    // Implementar modal con detalles completos
  }

  openDocumentUpload() {
    console.log('Opening document upload dialog');
    // Implementar modal de subida de documentos
  }

  reindexDocument(doc: DocumentInfo) {
    console.log('Reindexing document:', doc);
    // Implementar re-indexación
  }

  deleteDocument(doc: DocumentInfo) {
    console.log('Deleting document:', doc);
    // Implementar eliminación
  }

  refreshDocuments() {
    console.log('Actualizando documentos manualmente...');
    // Refrescar estadísticas primero, luego documentos
    this.loadVectorizationStats();
  }

  hasVectorizationData(): boolean {
    return this.stats.totalDocuments > 0 || this.stats.sourceDocuments > 0;
  }

  getVectorizationStatus(): string {
    if (this.stats.totalDocuments === 0) {
      return 'No hay datos de vectorización';
    } else if (this.stats.sourceDocuments > 0) {
      return `${this.stats.sourceDocuments} archivos vectorizados de ${this.stats.totalDocuments} total`;
    } else {
      return `${this.stats.totalDocuments} archivos pendientes de vectorización`;
    }
  }
}