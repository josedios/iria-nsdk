import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable, map } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface NSDKModule {
    name: string;
    file_path: string;
    file_name: string;
    line_count: number;
    char_count: number;
    function_count: number;
    functions: string[];
    size_kb: number;
    repository: string;
    repository_info?: any;
}

export interface RepositoryTreeNode {
    name: string;
    path: string;
    is_file: boolean;
    is_dir: boolean;
    depth: number;
    children: RepositoryTreeNode[];
    type: 'directory' | 'module' | 'screen' | 'include' | 'program' | 'config' | 'document' | 'other';
    file_count?: number;
    dir_count?: number;
    size_kb?: number;
    extension?: string;
    line_count?: number;
    char_count?: number;
    function_count?: number;
    functions?: string[];
    field_count?: number;
    fields?: string[];
    button_count?: number;
    buttons?: string[];
}

export interface RepositoryTreeResponse {
    repository_name: string;
    tree: RepositoryTreeNode;
}

export interface NSDKScreen {
    name: string;
    file_path: string;
    file_name: string;
    line_count: number;
    char_count: number;
    field_count: number;
    fields: string[];
    button_count: number;
    buttons: string[];
    size_kb: number;
    repository: string;
    repository_info?: any;
}

export interface ModulesResponse {
    total_modules: number;
    modules: NSDKModule[];
    repositories: any[];
}

export interface ScreensResponse {
    total_screens: number;
    screens: NSDKScreen[];
    repositories: any[];
}

export interface NSDKAnalysis {
  id: string;
  file_path: string;
  file_name: string;
  file_type: string;
  repository_name: string;
  line_count: number;
  char_count: number;
  size_kb: number;
  function_count: number;
  functions: string[];
  field_count: number;
  fields: string[];
  button_count: number;
  buttons: string[];
  module_name?: string;
  screen_name?: string;
  analysis_status: string;
  analysis_date?: string;
  metadata?: any;
  created_at?: string;
  updated_at?: string;
}

export interface AnalysisResponse {
  repository_name: string;
  total_analyses: number;
  analyses: NSDKAnalysis[];
}

export interface SyncStats {
  total_files: number;
  created: number;
  updated: number;
  skipped: number;
  errors: number;
}

export interface SyncResponse {
  repository_name: string;
  sync_stats: SyncStats;
  message: string;
}

export interface AnalysisStatus {
  repository_name: string;
  database_stats: {
    total_files: number;
    analyzed_files: number;
    pending_files: number;
    error_files: number;
    type_distribution: Record<string, number>;
    analysis_progress: number;
  };
  disk_stats: {
    total_files_on_disk: number;
    file_types_on_disk: Record<string, number>;
  };
  sync_status: 'in_sync' | 'out_of_sync';
  last_sync_check: string;
}

@Injectable({
    providedIn: 'root'
})
export class ModulesService {

    private apiUrl = environment.apiUrl;

    constructor(private http: HttpClient) { }

    /**
     * Obtiene todos los módulos NSDK del backend
     */
    getModules(): Observable<NSDKModule[]> {
        return this.http.get<ModulesResponse>(`${this.apiUrl}/modules`)
            .pipe(
                map(response => response.modules || [])
            );
    }

    /**
     * Obtiene todas las pantallas NSDK del backend
     */
    getScreens(): Observable<NSDKScreen[]> {
        return this.http.get<ScreensResponse>(`${this.apiUrl}/screens`)
            .pipe(
                map(response => response.screens || [])
            );
    }

    /**
 * Obtiene módulos y pantallas organizados por repositorio
 */
    getModulesAndScreens(): Observable<{ modules: NSDKModule[], screens: NSDKScreen[] }> {
        // Hacer dos llamadas paralelas: una para módulos y otra para pantallas
        return this.http.get<ModulesResponse>(`${this.apiUrl}/modules`)
            .pipe(
                map(response => {
                    const modules = response.modules || [];
                    // Por ahora, retornamos solo módulos. Las pantallas se obtendrán por separado
                    return { modules, screens: [] };
                })
            );
    }

    /**
     * Obtiene información de un repositorio específico
     */
    getRepositoryInfo(repoName: string): Observable<any> {
        return this.http.get(`${this.apiUrl}/repositories/${repoName}`);
    }

    /**
     * Inicia la vectorización de un repositorio
     */
    vectorizeRepository(repoUrl: string, branch: string = 'main', username?: string, token?: string): Observable<any> {
        return this.http.post(`${this.apiUrl}/vectorize/repository`, {
            repo_url: repoUrl,
            branch: branch,
            username: username,
            token: token
        });
    }

    /**
     * Obtiene estadísticas de vectorización
     */
    getVectorizationStats(): Observable<any> {
        return this.http.get(`${this.apiUrl}/vectorize/stats`);
    }

    /**
     * Obtiene la estructura de árbol completa de un repositorio
     */
    getRepositoryTree(repoName: string): Observable<RepositoryTreeResponse> {
        return this.http.get<RepositoryTreeResponse>(`${this.apiUrl}/repository-tree/${repoName}`);
    }

    /**
   * Sincroniza el análisis de archivos NSDK de un repositorio con la base de datos
   */
  syncRepositoryAnalysis(repoName: string, forceResync: boolean = false): Observable<SyncResponse> {
    const params = forceResync ? '?force_resync=true' : '';
    return this.http.post<SyncResponse>(`${this.apiUrl}/repositories/${repoName}/sync-analysis${params}`, {});
  }

  /**
   * Obtiene el estado del análisis de un repositorio
   */
  getRepositoryAnalysisStatus(repoName: string): Observable<AnalysisStatus> {
    return this.http.get<AnalysisStatus>(`${this.apiUrl}/repositories/${repoName}/analysis-status`);
  }

  /**
   * Obtiene los análisis de archivos NSDK de un repositorio
   */
  getRepositoryAnalysis(
    repoName: string, 
    fileType?: string, 
    status?: string
  ): Observable<AnalysisResponse> {
    let url = `${this.apiUrl}/repositories/${repoName}/analysis`;
    const params = new URLSearchParams();
    
    if (fileType) params.append('file_type', fileType);
    if (status) params.append('status', status);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    return this.http.get<AnalysisResponse>(url);
  }

  /**
   * Obtiene un análisis específico por ID
   */
  getAnalysisById(repoName: string, analysisId: string): Observable<NSDKAnalysis> {
    return this.http.get<NSDKAnalysis>(`${this.apiUrl}/repositories/${repoName}/analysis/${analysisId}`);
  }

  /**
   * Limpia análisis huérfanos de un repositorio
   */
  cleanupOrphanedAnalyses(repoName: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/repositories/${repoName}/cleanup-orphaned`, {});
  }
}
