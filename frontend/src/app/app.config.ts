import { ApplicationConfig, provideZoneChangeDetection, importProvidersFrom } from '@angular/core';
import { provideRouter } from '@angular/router';

import { routes } from './app.routes';
import { provideClientHydration } from '@angular/platform-browser';
import { provideHttpClient, withInterceptors, withFetch } from '@angular/common/http'; 
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import { provideToastr } from 'ngx-toastr';
import { provideMarkdown } from 'ngx-markdown';

import { authInterceptor } from './core/interceptors/auth.interceptor';

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideClientHydration(),
    provideHttpClient(
      withInterceptors([authInterceptor]),
      withFetch() // Add this line
    ),
    provideToastr({
      timeOut: 4000, // 4 seconds
      positionClass: 'toast-top-right',
      preventDuplicates: true,
    }),
    importProvidersFrom(BrowserAnimationsModule),
    provideMarkdown(),
  ]
};