import { Component, ElementRef, ViewChild } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HostListener } from '@angular/core';
import { Router } from '@angular/router';
import { TranscriptionService } from '../../services/transcription/transcription.service';
import { Transcription } from '../../models/transcription.model';
import { FormsModule } from '@angular/forms';
import { debounceTime, distinctUntilChanged, Subject } from 'rxjs';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './navbar.component.html',
  styleUrl: './navbar.component.css'
})
export class NavbarComponent {
  @ViewChild('searchInput') searchInput!: ElementRef<HTMLInputElement>;
  
  searchExpanded = false;
  currentLang = 'FR';
  searchTerm = '';
  searchResults: Transcription[] = [];
  showResults = false;
  isLoading = false;
  
  private searchSubject = new Subject<string>();

  constructor(private router: Router, private transcriptionService: TranscriptionService) {
    // Set up debounced search to avoid too many API calls
    this.searchSubject.pipe(
      debounceTime(300), // Wait 300ms after user stops typing
      distinctUntilChanged() // Only search if the term actually changed
    ).subscribe(searchTerm => {
      this.performSearch(searchTerm);
    });
  }

  toggleSearch(event: Event): void {
    event.stopPropagation();
    this.searchExpanded = !this.searchExpanded;
    
    if (this.searchExpanded) {
      // Focus the input after the DOM updates
      setTimeout(() => {
        if (this.searchInput) {
          this.searchInput.nativeElement.focus();
        }
      }, 100);
    } else {
      // Clear search when closing
      this.clearSearch();
    }
  }

  toggleLang() {
    this.currentLang = this.currentLang === 'FR' ? 'AR' : 'FR';
    // Optional: call a service to update app language here
  }

  @HostListener('document:click', ['$event'])
  handleClickOutside(event: Event): void {
    const target = event.target as HTMLElement;
    const searchContainer = target.closest('.search-container');
    
    // Only close if click is outside the search container
    if (this.searchExpanded && !searchContainer) {
      this.searchExpanded = false;
      this.clearSearch();
    }
  }

  goToDocumentation() {
    this.router.navigate(['/Home/documentation']);
  }

  onSearchInput(event: Event): void {
    const input = event.target as HTMLInputElement;
    const value = input.value.trim();
    this.searchTerm = value;
    
    if (value.length > 0) {
      this.searchSubject.next(value);
    } else {
      this.clearSearchResults();
    }
  }

  private performSearch(searchTerm: string): void {
    if (searchTerm.length < 2) {
      this.clearSearchResults();
      return;
    }

    this.isLoading = true;
    
    this.transcriptionService.getAllTranscriptions().subscribe({
      next: (results) => {
        this.searchResults = results.filter(pv =>
          pv.titreSceance && 
          pv.titreSceance.toLowerCase().includes(searchTerm.toLowerCase())
        ).slice(0, 10); // Limit to 10 results for performance
        
        this.showResults = true;
        this.isLoading = false;
      },
      error: (error) => {
        console.error('Search error:', error);
        this.searchResults = [];
        this.showResults = false;
        this.isLoading = false;
      }
    });
  }

  private clearSearchResults(): void {
    this.searchResults = [];
    this.showResults = false;
    this.isLoading = false;
  }

  private clearSearch(): void {
    this.searchTerm = '';
    this.clearSearchResults();
  }

  goToPvDetail(id: number, event?: Event): void {
    if (event) {
      event.stopPropagation();
    }
    
    this.router.navigate(['/Home/pv-detail', id]);
    this.searchExpanded = false;
    this.clearSearch();
  }

  // Handle keyboard navigation
  @HostListener('keydown', ['$event'])
  handleKeyDown(event: KeyboardEvent): void {
    if (this.searchExpanded && this.showResults) {
      switch (event.key) {
        case 'Escape':
          this.searchExpanded = false;
          this.clearSearch();
          break;
        case 'Enter':
          // Navigate to first result if available
          if (this.searchResults.length > 0) {
            this.goToPvDetail(this.searchResults[0].id);
          }
          break;
      }
    }
  }

  // Used by *ngFor trackBy to optimize rendering of PV search results
  trackByPvId(index: number, item: Transcription): number {
    return item.id;
  }

  theme = {
    navbar: '#333333'
  };
}
