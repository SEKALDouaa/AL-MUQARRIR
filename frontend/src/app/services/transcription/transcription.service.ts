import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Transcription } from '../../models/transcription.model';
import { StorageService } from '../storage/storage.service';

@Injectable({
  providedIn: 'root',
})
export class TranscriptionService {
  private apiBase = 'http://localhost:5000/api/transcriptions';

  constructor(
    private http: HttpClient,
    private storageService: StorageService
  ) {}

  private getAuthHeaders(): HttpHeaders {
    const token = this.storageService.get('access_token');
    return new HttpHeaders({
      Authorization: `Bearer ${token}`,
      'Content-Type': 'application/json',
    });
  }

  createTranscription(data: any): Observable<Transcription> {
    return this.http.post<Transcription>(this.apiBase, data, {
      headers: this.getAuthHeaders(),
    });
  }

  getTranscriptionById(id: number): Observable<Transcription> {
    return this.http.get<Transcription>(`${this.apiBase}/${id}`, {
      headers: this.getAuthHeaders(),
    });
  }

  getAllTranscriptions(): Observable<Transcription[]> {
    return this.http.get<Transcription[]>(this.apiBase, {
      headers: this.getAuthHeaders(),
    });
  }

  updateTranscription(id: number, data: any): Observable<Transcription> {
    return this.http.put<Transcription>(`${this.apiBase}/${id}`, data, {
      headers: this.getAuthHeaders(),
    });
  }

  deleteTranscription(id: number): Observable<any> {
    return this.http.delete(`${this.apiBase}/${id}`, {
      headers: this.getAuthHeaders(),
    });
  }

  searchTranscriptions(query: string): Observable<Transcription[]> {
    const params = new HttpParams().set('query', query);
    return this.http.get<Transcription[]>(`${this.apiBase}/search`, {
      headers: this.getAuthHeaders(),
      params: params,
    });
  }

  generateDeroulement(transcriptionId: number): Observable<Transcription> {
    return this.http.post<Transcription>(
      `${this.apiBase}/${transcriptionId}/deroulement`,
      {},
      {
        headers: this.getAuthHeaders(),
      }
    );
  }

  generateAnalyse(transcriptionId: number): Observable<Transcription> {
    return this.http.post<Transcription>(
      `${this.apiBase}/${transcriptionId}/analyse`,
      {},
      {
        headers: this.getAuthHeaders(),
      }
    );
  }

  exportPvDocx(transcriptionId: number): Observable<Blob> {
    return this.http.get(`${this.apiBase}/${transcriptionId}/export/pv/docx`, {
      headers: this.getAuthHeaders(),
      responseType: 'blob',
    });
  }

  exportPvPdf(transcriptionId: number): Observable<Blob> {
    return this.http.get(`${this.apiBase}/${transcriptionId}/export/pv/pdf`, {
      headers: this.getAuthHeaders(),
      responseType: 'blob',
    });
  }

  exportAnalysisDocx(transcriptionId: number): Observable<Blob> {
    return this.http.get(
      `${this.apiBase}/${transcriptionId}/export/analysis/docx`,
      {
        headers: this.getAuthHeaders(),
        responseType: 'blob',
      }
    );
  }

  exportAnalysisPdf(transcriptionId: number): Observable<Blob> {
    return this.http.get(
      `${this.apiBase}/${transcriptionId}/export/analysis/pdf`,
      {
        headers: this.getAuthHeaders(),
        responseType: 'blob',
      }
    );
  }

  getNgrokUrl(): Observable<{ ngrok_url: string }> {
    return this.http.get<{ ngrok_url: string }>(`${this.apiBase}/ngrok-url`, {
      headers: this.getAuthHeaders(),
    });
  }
}
