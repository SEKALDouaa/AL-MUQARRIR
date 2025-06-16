import { HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { StorageService } from '../../services/storage/storage.service'; // adjust the path if needed

export const authInterceptor: HttpInterceptorFn = (req, next) => {
const storageService = inject(StorageService);
const token = storageService.get('token');

if (token) {
    const authReq = req.clone({
      setHeaders: {
        Authorization: `Bearer ${token}`
      }
    });
    return next(authReq);
  }

  return next(req);
};
