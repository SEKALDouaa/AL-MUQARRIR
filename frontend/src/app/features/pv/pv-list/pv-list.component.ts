import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';               // pour *ngFor, *ngIf, ...
import { Router } from '@angular/router';

import { TranscriptionService } from '../../../services/transcription/transcription.service';
import { Transcription } from '../../../models/transcription.model';

@Component({
selector: 'app-pv-list',
standalone: true,             // ← ici tu rends le composant standalone
imports: [CommonModule],      // ← tu dois importer ici les modules utilisés dans le template
templateUrl: './pv-list.component.html',
styleUrls: ['./pv-list.component.css']
})
export class PvListComponent implements OnInit {
transcriptions: Transcription[] = [];

constructor(
    private transcriptionService: TranscriptionService,
    private router: Router
  ) {}

  ngOnInit(): void {
    this.transcriptionService.getAllTranscriptions().subscribe({
      next: (data) => this.transcriptions = data,
      error: (err) => console.error(err)
    });
  }

  goToDetails(id: number) {
    this.router.navigate(['/Home/pv-detail', id]);
  }
}
