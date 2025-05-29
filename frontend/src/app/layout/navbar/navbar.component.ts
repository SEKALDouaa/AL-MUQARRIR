import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HostListener } from '@angular/core';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css'
})
export class NavbarComponent {
  searchExpanded = false;
  currentLang = 'FR'

  toggleSearch(event: Event): void {
    this.searchExpanded = !this.searchExpanded;
    event.stopPropagation();
  }

  toggleLang() {
    this.currentLang = this.currentLang === 'FR' ? 'AR' : 'FR';
    // Optional: call a service to update app language here
  }

  @HostListener('document:click', ['$event'])
  handleClickOutside(event: Event): void {
    if (this.searchExpanded) {
      this.searchExpanded = false;
    }
  }

  theme = {
    navbar: '#333333'
  };
}
