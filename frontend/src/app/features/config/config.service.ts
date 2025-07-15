import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface Configuration {
    id?: string;
    name: string;
    description?: string;
    config_data: any;
    created_at?: string;
    updated_at?: string;
}

@Injectable({ providedIn: 'root' })
export class ConfigService {
    private apiUrl = environment.apiUrl + '/configurations';

    constructor(private http: HttpClient) { }

    getAll(): Observable<Configuration[]> {
        return this.http.get<Configuration[]>(this.apiUrl);
    }

    getById(id: string): Observable<Configuration> {
        return this.http.get<Configuration>(`${this.apiUrl}/${id}`);
    }

    create(config: Configuration): Observable<Configuration> {
        return this.http.post<Configuration>(this.apiUrl, config);
    }

    update(id: string, config: Configuration): Observable<Configuration> {
        return this.http.put<Configuration>(`${this.apiUrl}/${id}`, config);
    }

    delete(id: string): Observable<any> {
        return this.http.delete(`${this.apiUrl}/${id}`);
    }
} 