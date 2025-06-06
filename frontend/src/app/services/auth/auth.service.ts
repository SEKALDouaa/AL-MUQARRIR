import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';
import { Observable } from 'rxjs';
import { StorageService } from '../storage/storage.service';  // Assure-toi du bon chemin

@Injectable({
providedIn: 'root'
})
export class AuthService {
private baseUrl = 'http://localhost:5000/api';

constructor(
    private http: HttpClient,
    private storageService: StorageService
  ) {}

  login(credentials: { email: string; password: string }): Observable<{ access_token: string }> {
    return this.http.post<{ access_token: string }>(`${this.baseUrl}/login`, credentials)
      .pipe(
        tap(response => {
          this.storageService.set('access_token', response.access_token);
        })
      );
  }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/register`, userData);
  }

  getToken(): string | null {
    return this.storageService.get('access_token');
  }

  saveToken(token: string): void {
    this.storageService.set('access_token', token);
  }

  logout(): void {
    this.storageService.remove('access_token');
  }
}
