import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TranscriptionService } from '../../services/transcription/transcription.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-view-transcription',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './view-transcription.component.html',
  styleUrls: ['./view-transcription.component.css']
})
export class ViewTranscriptionComponent implements OnInit {
  pvId: string | null = null;
  transcription: { speaker: string, text: string }[] = [];
  isLoading = true;

  constructor(
    private route: ActivatedRoute,
    private transcriptionService: TranscriptionService
  ) {}

  ngOnInit(): void {
    this.pvId = this.route.snapshot.paramMap.get('id');
    if (this.pvId) {
      this.transcriptionService.getTranscriptionById(Number(this.pvId)).subscribe({
        next: (pv) => {
          try {
            const parsed = typeof pv.Transcription === 'string' ? JSON.parse(pv.Transcription) : pv.Transcription;
            this.transcription = Array.isArray(parsed) ? parsed : [];
          } catch {
            this.transcription = [];
          }
          this.isLoading = false;
        },
        error: () => { this.isLoading = false; }
      });
    }
  }
}
