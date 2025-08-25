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
}
