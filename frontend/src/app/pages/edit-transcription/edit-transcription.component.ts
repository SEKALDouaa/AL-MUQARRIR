import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { TranscriptionService } from '../../services/transcription/transcription.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-edit-transcription',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './edit-transcription.component.html',
  styleUrls: ['./edit-transcription.component.css']
})
export class EditTranscriptionComponent implements OnInit {
  pvId: string | null = null;
  transcription: { speaker: string, text: string }[] = [];
  isLoading = true;
  isSaving = false;

  constructor(
    private route: ActivatedRoute,
    public router: Router,
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

  onSave() {
    if (this.pvId) {
      this.isSaving = true;
      this.transcriptionService.updateTranscription(Number(this.pvId), {
        Transcription: this.transcription
      }).subscribe({
        next: () => {
          // Call generateDeroulement after successful update
          this.transcriptionService.generateDeroulement(Number(this.pvId)).subscribe({
            next: () => {
              // Call generateAnalyse after generateDeroulement
              this.transcriptionService.generateAnalyse(Number(this.pvId)).subscribe({
                next: () => {
                  this.router.navigate(['/Home', 'pv', this.pvId, 'view-transcription']);
                },
                error: (err) => {
                  console.error('Échec de la génération de l\'analyse', err);
                  // Still navigate even if generation fails
                  this.router.navigate(['/Home', 'pv', this.pvId, 'view-transcription']);
                }
              });
            },
            error: (err) => {
              console.error('Échec de la génération du déroulement', err);
              // Still navigate even if generation fails
              this.router.navigate(['/Home', 'pv', this.pvId, 'view-transcription']);
            }
          });
        },
        error: (err) => {
          this.isSaving = false;
          console.error('Failed to update transcription', err);
        }
      });
    }
  }
}
