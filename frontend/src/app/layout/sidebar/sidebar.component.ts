import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Router } from '@angular/router';
import { AuthService } from '../../services/auth/auth.service'; // Adjust the path if needed

@Component({
selector: 'app-sidebar',
standalone: true,
imports: [CommonModule, RouterModule],
templateUrl: './sidebar.component.html',
styleUrl: './sidebar.component.css'
})
export class SidebarComponent {
isSidebarCollapsed = false;

constructor(private authService: AuthService, private router: Router) {}

  toggleSidebar(): void {
    this.isSidebarCollapsed = !this.isSidebarCollapsed;
  }

  logout(): void {
    this.authService.logout(); // clears sessionStorage
    this.router.navigate(['/']); // redirect to login or landing page
  }
}
