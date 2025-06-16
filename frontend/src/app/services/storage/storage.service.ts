import { Injectable } from '@angular/core';

@Injectable({
providedIn: 'root'
})
export class StorageService {

  set(key: string, value: string): void {
    if (typeof window !== 'undefined') {
      sessionStorage.setItem(key, value);
    }
  }

  get(key: string): string | null {
    if (typeof window !== 'undefined') {
      return sessionStorage.getItem(key);
    }
    return null;
  }

  remove(key: string): void {
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem(key);
    }
  }

  clear(): void {
    if (typeof window !== 'undefined') {
      sessionStorage.clear();
    }
  }
}
