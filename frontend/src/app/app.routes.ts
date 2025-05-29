import { Routes } from '@angular/router';
import { MainLayoutComponent } from './layout/main-layout/main-layout.component';
import { PvFormComponent } from './pages/pv-form/pv-form.component';

export const routes: Routes = [
{
path: '',
component: MainLayoutComponent,
children: [
{ path: 'pv', component: PvFormComponent },
]
},
// Optionnel : rediriger toute autre route vers 'pv'
//{ path: '**', redirectTo: 'pv' }
];
