import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { tap } from 'rxjs/operators';
import { Observable } from 'rxjs';

@Injectable({
providedIn: 'root'
})
export class AuthService {
private baseUrl = 'http://localhost:5000/api';

constructor(private http: HttpClient) {}

  login(credentials: { email: string; password: string }): Observable<{ access_token: string }> {
    return this.http.post<{ access_token: string }>(`${this.baseUrl}/login`, credentials)
      .pipe(
        tap(response => {
          localStorage.setItem('access_token', response.access_token);
        })
      );
  }

  register(userData: any): Observable<any> {
    return this.http.post(`${this.baseUrl}/register`, userData);
  }

  getToken(): string | null {
    return localStorage.getItem('access_token');
  }

  saveToken(token: string): void {
    localStorage.setItem('access_token', token);
  }

  logout(): void {
    localStorage.removeItem('access_token');
  }
}
