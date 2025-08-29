import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface VectorizeRepositoryRequest {
    repo_url: string;
    branch: string;
    username?: string;
    token?: string;
}

export interface VectorizeModuleRequest {
    module_path: string;
    repo_url: string;
    branch: string;
}

export interface SearchCodeRequest {
    query: string;
    limit: number;
}

export interface VectorizationBatch {
    id: string;
    name: string;
    batch_type: string;
    source_repo_url: string;
    source_repo_branch: string;
    status: string;
    total_files: number;
    processed_files: number;
    successful_files: number;
    failed_files: number;
    progress: number;
    success_rate: number;
    started_at?: string;
    completed_at?: string;
    created_at: string;
    updated_at: string;
}

export interface VectorizationStats {
    total_files: number;
    vectorized_files: number;
    pending_files: number;
    error_files: number;
    last_vectorization?: string;
    by_repository_type?: {
        nsdk: {
            total: number;
            vectorized: number;
            pending: number;
            error: number;
        };
        angular: {
            total: number;
            vectorized: number;
            pending: number;
            error: number;
        };
        spring_boot: {
            total: number;
            vectorized: number;
            pending: number;
            error: number;
        };
    };
}

export interface SearchResult {
    id: string;
    score: number;
    metadata: any;
}

export interface SearchResponse {
    query: string;
    results: SearchResult[];
    total_results: number;
}

@Injectable({
    providedIn: 'root'
})
export class KnowledgeService {
    private apiUrl = environment.apiUrl;

    constructor(private http: HttpClient) { }

    // Vectorización de repositorios
    vectorizeRepository(request: VectorizeRepositoryRequest): Observable<any> {
        return this.http.post(`${this.apiUrl}/vectorize/repository`, request);
    }

    vectorizeModule(request: VectorizeModuleRequest): Observable<any> {
        return this.http.post(`${this.apiUrl}/vectorize/module`, request);
    }

    // Estadísticas y estado
    getVectorizationStats(): Observable<VectorizationStats> {
        return this.http.get<VectorizationStats>(`${this.apiUrl}/vectorize/stats`);
    }

    getBatchStatus(batchId: string): Observable<VectorizationBatch> {
        return this.http.get<VectorizationBatch>(`${this.apiUrl}/vectorize/batch/${batchId}`);
    }

    cancelBatch(batchId: string): Observable<any> {
        return this.http.post(`${this.apiUrl}/vectorize/batch/${batchId}/cancel`, {});
    }

    // Búsqueda de código
    searchSimilarCode(request: SearchCodeRequest): Observable<SearchResponse> {
        return this.http.post<SearchResponse>(`${this.apiUrl}/vectorize/search`, request);
    }

    // Búsqueda semántica avanzada
    searchBySemanticQuery(query: string, limit: number = 10): Observable<SearchResponse> {
        return this.searchSimilarCode({ query, limit });
    }

    // Búsqueda por tipo de archivo
    searchByFileType(fileType: string, query: string, limit: number = 10): Observable<SearchResponse> {
        const enhancedQuery = `${query} file_type:${fileType}`;
        return this.searchSimilarCode({ query: enhancedQuery, limit });
    }

    // Búsqueda por módulo
    searchByModule(moduleName: string, query: string, limit: number = 10): Observable<SearchResponse> {
        const enhancedQuery = `${query} module:${moduleName}`;
        return this.searchSimilarCode({ query: enhancedQuery, limit });
    }

    // Búsqueda por contenido específico
    searchByContent(content: string, limit: number = 10): Observable<SearchResponse> {
        return this.searchSimilarCode({ query: content, limit });
    }

    // Obtener archivos vectorizados recientemente
    getRecentVectorizedFiles(limit: number = 20): Observable<any[]> {
        // TODO: Implementar endpoint para archivos recientes
        return this.http.get<any[]>(`${this.apiUrl}/vectorize/recent-files?limit=${limit}`);
    }

    // Obtener archivos por estado
    getFilesByStatus(status: string, limit: number = 50): Observable<any[]> {
        // TODO: Implementar endpoint para archivos por estado
        return this.http.get<any[]>(`${this.apiUrl}/vectorize/files/status/${status}?limit=${limit}`);
    }

    // Obtener archivos por tipo
    getFilesByType(fileType: string, limit: number = 50): Observable<any[]> {
        // TODO: Implementar endpoint para archivos por tipo
        return this.http.get<any[]>(`${this.apiUrl}/vectorize/files/type/${fileType}?limit=${limit}`);
    }

    // Obtener archivos por módulo
    getFilesByModule(moduleName: string, limit: number = 50): Observable<any[]> {
        // TODO: Implementar endpoint para archivos por módulo
        return this.http.get<any[]>(`${this.apiUrl}/vectorize/files/module/${moduleName}?limit=${limit}`);
    }

    // Análisis de similitud entre archivos
    analyzeFileSimilarity(fileId1: string, fileId2: string): Observable<any> {
        // TODO: Implementar endpoint para análisis de similitud
        return this.http.get<any>(`${this.apiUrl}/vectorize/similarity/${fileId1}/${fileId2}`);
    }

    // Obtener recomendaciones de archivos relacionados
    getRelatedFiles(fileId: string, limit: number = 10): Observable<any[]> {
        // TODO: Implementar endpoint para archivos relacionados
        return this.http.get<any[]>(`${this.apiUrl}/vectorize/related/${fileId}?limit=${limit}`);
    }

    // Exportar resultados de búsqueda
    exportSearchResults(searchResults: SearchResult[], format: 'json' | 'csv' | 'excel' = 'json'): Observable<any> {
        // TODO: Implementar endpoint para exportación
        return this.http.post(`${this.apiUrl}/vectorize/export`, {
            results: searchResults,
            format: format
        });
    }

    // Limpiar vector store
    clearVectorStore(): Observable<any> {
        // TODO: Implementar endpoint para limpiar vector store
        return this.http.post(`${this.apiUrl}/vectorize/clear`, {});
    }

    // Reindexar archivos existentes
    reindexFiles(fileIds: string[]): Observable<any> {
        // TODO: Implementar endpoint para reindexación
        return this.http.post(`${this.apiUrl}/vectorize/reindex`, { file_ids: fileIds });
    }

    // Obtener métricas de rendimiento
    getPerformanceMetrics(): Observable<any> {
        // TODO: Implementar endpoint para métricas de rendimiento
        return this.http.get<any>(`${this.apiUrl}/vectorize/metrics/performance`);
    }

    // Obtener métricas de calidad
    getQualityMetrics(): Observable<any> {
        // TODO: Implementar endpoint para métricas de calidad
        return this.http.get<any>(`${this.apiUrl}/vectorize/metrics/quality`);
    }
}
