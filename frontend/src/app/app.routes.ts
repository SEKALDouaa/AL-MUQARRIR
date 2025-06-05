import { Routes } from '@angular/router';
import { MainLayoutComponent } from './layout/main-layout/main-layout.component';
import { PvFormComponent } from './pages/pv-form/pv-form.component';
import { AuthComponent } from './pages/auth/auth.component';
import { LandingLayoutComponent } from './layout/landing-layout/landing-layout.component';
import { LandingComponent } from './pages/landing/landing.component';

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
// Add more secured routes here
]
},

// Catch-all redirect
{ path: '**', redirectTo: '' }
];
