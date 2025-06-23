import { Component, OnInit } from '@angular/core';
import { FormBuilder, FormGroup } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
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
  status: string = 'Select an audio file to begin';
  statusClass: string = 'status';
  results: any[] = [];
  ngrokUrl: string = '';
  pvId: string | null = null;
  isLoading = false;

  constructor(
    private fb: FormBuilder,
    private route: ActivatedRoute,
    private transcriptionService: TranscriptionService
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
        console.log('Ngrok URL:', this.ngrokUrl); // Debug log
      },
      error: () => (this.status = 'Failed to fetch API URL'),
    });
  }

  onFileChange(event: any) {
    const file = event.target.files[0];
    this.form.patchValue({ file });
    this.status = file
      ? `Ready to transcribe: ${file.name}`
      : 'Select an audio file to begin transcription';
    this.statusClass = 'status';
  }

  async submit() {
    if (!this.form.value.file || !this.ngrokUrl) return;
    this.isLoading = true;
    this.status = 'Transcribing...';
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
      this.status = 'Transcription complete';
      this.statusClass = 'status';
    } catch (error: any) {
      this.status = `Error: ${error.message}`;
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
    this.status = 'Select an audio file to begin transcription';
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
}
