import { Component, OnInit } from '@angular/core';
import { TranscriptionService } from '../../../services/transcription/transcription.service';
import { Transcription } from '../../../models/transcription.model';
import { Router } from '@angular/router';

@Component({
selector: 'app-transcription-list',
templateUrl: './transcription-list.component.html',
styleUrls: ['./transcription-list.component.css']
})
export class TranscriptionListComponent implements OnInit {
transcriptions: Transcription[] = [];

constructor(private transcriptionService: TranscriptionService, private router: Router) {}

  ngOnInit(): void {
    this.transcriptionService.getAllTranscriptions().subscribe({
      next: (data) => this.transcriptions = data,
      error: (err) => console.error(err)
    });
  }

  goToDetails(id: number) {
    this.router.navigate(['/transcriptions', id]);
  }
}
