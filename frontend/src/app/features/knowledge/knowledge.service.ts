import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface NSDKDocument {
    id: string;
    name: string;
    file_path: string;
    file_size: number;
    status: string;
    total_chunks: number;
    created_at: string;
    updated_at: string;
}

export interface DocumentUploadResponse {
    status: string;
    message: string;
    document_id: string;
    document_name: string;
}

export interface DocumentQueryResponse {
    status: string;
    query: string;
    result: string;
}

export interface DocumentStats {
    total_documents: number;
    total_chunks: number;
    documents: Array<{
        document_id: string;
        chunk_count: number;
        total_text_length: number;
    }>;
}

export interface SearchCodeRequest {
    query: string;
    limit: number;
}

export interface VectorizationBatch {
    id: string;
    status: string;
    processed_files: number;
    total_files: number;
}

export interface VectorizationStats {
    total_files: number;
    vectorized_files: number;
    last_vectorization: string;
    by_repository_type?: {
        nsdk?: { total: number };
        angular?: { total: number };
        spring_boot?: { total: number };
    };
}

export interface VectorizeRepositoryRequest {
    config_id: string;
    repo_type: string;
    branch: string;
}

@Injectable({
    providedIn: 'root'
})
export class KnowledgeService {
    private apiUrl = environment.apiUrl;

    constructor(private http: HttpClient) { }

    /**
     * Sube y procesa un documento PDF de NSDK
     */
    uploadDocument(filePath: string, documentName: string): Observable<DocumentUploadResponse> {
        return this.http.post<DocumentUploadResponse>(`${this.apiUrl}/nsdk-documents/upload`, {
            file_path: filePath,
            document_name: documentName
        });
    }

    /**
     * Obtiene el estado de procesamiento de un documento
     */
    getDocumentStatus(documentId: string): Observable<{ status: string, document: NSDKDocument }> {
        return this.http.get<{ status: string, document: NSDKDocument }>(`${this.apiUrl}/nsdk-documents/${documentId}/status`);
    }

    /**
     * Obtiene todos los documentos NSDK procesados
     */
    getAllDocuments(): Observable<{ status: string, documents: NSDKDocument[] }> {
        return this.http.get<{ status: string, documents: NSDKDocument[] }>(`${this.apiUrl}/nsdk-documents`);
    }

    /**
     * Consulta la documentación NSDK
     */
    queryDocumentation(query: string, context: string = ''): Observable<DocumentQueryResponse> {
        return this.http.post<DocumentQueryResponse>(`${this.apiUrl}/nsdk-documents/query`, {
            query: query,
            context: context
        });
    }

    /**
     * Obtiene estadísticas de la documentación NSDK
     */
    getDocumentationStats(): Observable<{ status: string, stats: DocumentStats }> {
        return this.http.get<{ status: string, stats: DocumentStats }>(`${this.apiUrl}/nsdk-documents/stats`);
    }

    /**
     * Prueba la indexación de documentos NSDK
     */
    testDocumentIndexing(): Observable<{ status: string, test_results: any }> {
        return this.http.post<{ status: string, test_results: any }>(`${this.apiUrl}/nsdk-documents/test-indexing`, {});
    }

    /**
     * Procesa un documento PDF existente en NSDK-DOCS
     */
    processExistingDocument(documentName: string): Observable<DocumentUploadResponse> {
        return this.http.post<DocumentUploadResponse>(`${this.apiUrl}/nsdk-documents/process-existing`,
            documentName,
            {
                headers: {
                    'Content-Type': 'text/plain'
                }
            }
        );
    }

    /**
     * Obtiene la lista de documentos PDF disponibles en NSDK-DOCS
     */
    getAvailableDocuments(): Observable<{ status: string, documents: any[], total_count: number }> {
        return this.http.get<{ status: string, documents: any[], total_count: number }>(`${this.apiUrl}/nsdk-documents/available`);
    }

    /**
     * Vectoriza un repositorio
     */
    vectorizeRepository(request: VectorizeRepositoryRequest): Observable<any> {
        return this.http.post<any>(`${this.apiUrl}/vectorize/repository`, request);
    }

    /**
     * Obtiene el estado de un batch de vectorización
     */
    getBatchStatus(batchId: string): Observable<VectorizationBatch> {
        return this.http.get<VectorizationBatch>(`${this.apiUrl}/vectorize/batch/${batchId}/status`);
    }

    /**
     * Obtiene estadísticas de vectorización
     */
    getVectorizationStats(): Observable<VectorizationStats> {
        return this.http.get<VectorizationStats>(`${this.apiUrl}/vectorize/embeddings/stats`);
    }

    /**
     * Busca código similar
     */
    searchSimilarCode(request: SearchCodeRequest): Observable<{ results: any[] }> {
        return this.http.post<{ results: any[] }>(`${this.apiUrl}/vectorize/search`, request);
    }
}