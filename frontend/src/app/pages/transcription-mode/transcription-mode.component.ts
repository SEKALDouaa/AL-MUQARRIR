import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-transcription-mode',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './transcription-mode.component.html',
  styleUrls: ['./transcription-mode.component.css']
})
export class TranscriptionModeComponent implements OnInit {
  pvId: string | null = null;

  constructor(
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    // This code runs when the component is initialized
    this.pvId = this.route.snapshot.paramMap.get('id');
  }

  goToBatchTranscription() {
    // Navigate to the batch transcription page, passing the ID
    if (this.pvId) {
      this.router.navigate(['/Home', 'batch-transcription', this.pvId]);
    }
  }

  goToRealtimeTranscription() {
    // Navigate to the real-time transcription page, passing the ID
    if (this.pvId) {
      this.router.navigate(['/Home', 'realtime-transcription', this.pvId]);
    }
  }
}