import { Routes } from '@angular/router';
import { MainLayoutComponent } from './layout/main-layout/main-layout.component';
import { PvFormComponent } from './pages/pv-form/pv-form.component';
import { AuthComponent } from './pages/auth/auth.component'; // importe ton composant

export const routes: Routes = [
// Route sans layout (ex: login/signup)
{ path: 'auth', component: AuthComponent },

// Routes avec layout principal
{
path: '',
component: MainLayoutComponent,
children: [
{ path: 'pv', component: PvFormComponent },
// tu peux ajouter d'autres enfants ici
]
},

// Redirection par défaut
{ path: '', redirectTo: 'auth', pathMatch: 'full' },

// Redirection en cas de mauvaise route
{ path: '**', redirectTo: 'auth' }
];
