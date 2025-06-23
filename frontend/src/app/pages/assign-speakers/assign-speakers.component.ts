import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TranscriptionService } from '../../services/transcription/transcription.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-assign-speakers',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './assign-speakers.component.html',
  styleUrls: ['./assign-speakers.component.css']
})
export class AssignSpeakersComponent implements OnInit {
  pvId: string | null = null;
  members: string[] = [];
  transcription: any = [];
  speakerLabels: string[] = [];
  speakerMapping: { [key: string]: string | null } = {};
  isLoading = true;

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private transcriptionService: TranscriptionService
  ) {}

  ngOnInit(): void {
    this.pvId = this.route.snapshot.paramMap.get('id');
    if (this.pvId) {
      this.transcriptionService.getTranscriptionById(Number(this.pvId)).subscribe({
        next: (pv) => {
          this.members = (pv.Membres || '').split(',').map(m => m.trim()).filter(m => m);
          try {
            // Ensure the transcription is always parsed as an array
            const parsed = typeof pv.Transcription === 'string' ? JSON.parse(pv.Transcription) : pv.Transcription;
            this.transcription = Array.isArray(parsed) ? parsed : [];
          } catch {
            this.transcription = [];
          }
          // Get unique speaker labels from the array
          this.speakerLabels = Array.from(new Set(this.transcription.map((seg: any) => seg.speaker)));
          this.speakerLabels.forEach(s => this.speakerMapping[s] = null);
          this.isLoading = false;
        },
        error: () => { this.isLoading = false; }
      });
    }
  }

  onSaveMapping() {
    // Remap the transcription array with real member names
    const remappedTranscription = this.transcription.map((seg: any) => {
      const mapped = this.speakerMapping[seg.speaker];
      return {
        speaker: mapped ? mapped : seg.speaker,
        text: seg.text
      };
    });
    if (this.pvId) {
      this.transcriptionService.updateTranscription(Number(this.pvId), {
        Transcription: remappedTranscription
      }).subscribe({
        next: () => {
          // Optionally show a success message
        },
        error: (err) => {
          // Optionally show an error message
          console.error('Failed to update transcription', err);
        }
      });
    }
  }

  onNext() {
    // Optionally, update the backend with the mapping or new transcription
    if (this.pvId) {
      this.router.navigate(['/Home', 'pv', this.pvId, 'next-step']);
    }
  }

  // Returns the transcription as a list of segments for UI display (like batch-transcription)
  getTranscriptionSegments(): { speaker: string, text: string }[] {
    // Already an array of segments
    return this.transcription;
  }
}
