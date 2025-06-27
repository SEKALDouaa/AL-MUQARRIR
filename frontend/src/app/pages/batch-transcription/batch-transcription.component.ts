import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { TranscriptionService } from '../../services/transcription/transcription.service';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-batch-transcription',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './batch-transcription.component.html',
  styleUrls: ['./batch-transcription.component.css'],
})
export class BatchTranscriptionComponent implements OnInit {
  form: FormGroup;
  status: string = 'Sélectionnez un fichier audio pour commencer';
  statusClass: string = 'status';
  results: any[] = [];
  ngrokUrl: string = '';
  pvId: string | null = null;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private transcriptionService: TranscriptionService,
    private router: Router
  ) {
    this.form = this.fb.group({
      file: [null],
    });
  }

  ngOnInit(): void {
    this.pvId = this.route.snapshot.paramMap.get('id');
    this.transcriptionService.getNgrokUrl().subscribe({
      next: (res) => {
        this.ngrokUrl = res.ngrok_url;
      },
      error: () => (this.status = 'Échec de la récupération de l’URL de l’API'),
    });
  }

  onFileChange(event: any) {
    const file = event.target.files[0];
    this.form.patchValue({ file });
    this.status = file
      ? `Prêt à transcrire : ${file.name}`
      : 'Sélectionnez un fichier audio pour commencer la transcription';
    this.statusClass = 'status';
  }

  async submit() {
    if (!this.form.value.file || !this.ngrokUrl) return;
    this.isLoading = true;
    this.status = 'Transcription en cours...';
    this.statusClass = 'status loading';
    this.results = [];

    const formData = new FormData();
    formData.append('file', this.form.value.file);

    try {
      const response = await fetch(`${this.ngrokUrl}/process_audio`, {
        method: 'POST',
        body: formData,
      });
      if (!response.ok)
        throw new Error((await response.text()) || response.statusText);
      const data = await response.json();
      this.results = data.result;
      this.status = 'Transcription terminée';
      this.statusClass = 'status';
      // Update the transcription in the backend
      if (this.pvId && this.results.length) {
        // Save as an array of segments: [{ speaker: string, text: string }, ...]
        const segments = this.results.map((item) => {
          const speaker = this.getSpeaker(item);
          const text = this.getText(item);
          return { speaker, text };
        });
        this.transcriptionService
          .updateTranscription(Number(this.pvId), {
            Transcription: segments,
          })
          .subscribe({
            next: () => console.log('Transcription updated successfully'),
            error: (err) => console.error('Failed to update transcription:', err),
          });
      }
    } catch (error: any) {
      this.status = `Erreur : ${error.message}`;
      this.statusClass = 'status error';
    } finally {
      this.isLoading = false;
    }
  }

  getSpeaker(item: any): string {
    return Object.keys(item)[0];
  }

  getText(item: any): string {
    return item[this.getSpeaker(item)];
  }

  isDragOver = false;

  formatFileSize(bytes: number): string {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }

  clearFile() {
    this.form.patchValue({ file: null });
    this.status = 'Sélectionnez un fichier audio pour commencer la transcription';
    this.statusClass = 'status';
  }

  clearResults() {
    this.results = [];
  }

  getStatusClass(): string {
    if (this.isLoading) return 'status-card status-loading';
    if (this.status.includes('Error')) return 'status-card status-error';
    if (this.status.includes('complete')) return 'status-card status-success';
    return 'status-card status-default';
  }

  goToAssignSpeakers() {
    if (this.pvId) {
      this.router.navigate(['/Home/pv', this.pvId, 'assign-speakers']);
    }
  }
}
