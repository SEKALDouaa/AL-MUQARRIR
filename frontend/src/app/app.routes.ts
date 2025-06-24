import { Routes } from '@angular/router';
import { MainLayoutComponent } from './layout/main-layout/main-layout.component';
import { PvFormComponent } from './pages/pv-form/pv-form.component';
import { AuthComponent } from './pages/auth/auth.component';
import { LandingLayoutComponent } from './layout/landing-layout/landing-layout.component';
import { LandingComponent } from './pages/landing/landing.component';
import { AnalysisListComponent } from './features/analyses/analysis-list/analysis-list.component'
import { PvListComponent } from './features/pv/pv-list/pv-list.component'
import { TranscriptionListComponent } from './features/transcriptions/transcription-list/transcription-list.component'
import { TranscriptionDetailComponent } from './features/transcriptions/transcription-detail/transcription-detail.component'
import { AnalysisDetailComponent } from './features/analyses/analysis-detail/analysis-detail.component'
import { PvDetailComponent } from './features/pv/pv-detail/pv-detail.component'
import { TranscriptionModeComponent } from './pages/transcription-mode/transcription-mode.component'
import { BatchTranscriptionComponent } from './pages/batch-transcription/batch-transcription.component';

export const routes: Routes = [
// Route without layout (auth)
{ path: 'auth', component: AuthComponent },

// Landing route with its own layout (navbar + footer)
{
path: '',
component: LandingLayoutComponent,
children: [
{ path: '', component: LandingComponent }
]
},

// Authenticated routes with main layout
{
path: 'Home',
component: MainLayoutComponent,
children: [
{ path: 'pv-form', component: PvFormComponent },
{ path: 'analysis-list', component: AnalysisListComponent },
{ path: 'pv-list', component: PvListComponent },
{ path: 'transcriptions-list', component: TranscriptionListComponent },
{ path: 'transcriptions-detail/:id', component: TranscriptionDetailComponent },
{ path: 'analysis-detail/:id', component: AnalysisDetailComponent },
{ path: 'pv-detail/:id', component: PvDetailComponent },
{ path: 'pv/:id/select-transcription-mode', component: TranscriptionModeComponent },
{ path: 'batch-transcription/:id', component: BatchTranscriptionComponent },
{ path: 'pv/:id/assign-speakers', loadComponent: () => import('./pages/assign-speakers/assign-speakers.component').then(m => m.AssignSpeakersComponent) },
{ path: 'pv/:id/edit-transcription', loadComponent: () => import('./pages/edit-transcription/edit-transcription.component').then(m => m.EditTranscriptionComponent) },
{ path: 'pv/:id/view-transcription', loadComponent: () => import('./pages/view-transcription/view-transcription.component').then(m => m.ViewTranscriptionComponent) },
{ path: 'realtime-transcription/:id', loadComponent: () => import('./pages/realtime-transcription/realtime-transcription.component').then(m => m.RealtimeTranscriptionComponent) },
]
},

// Catch-all redirect
{ path: '**', redirectTo: '' }
];
