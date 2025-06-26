import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Transcription } from '../../../models/transcription.model';
import { TranscriptionService } from '../../../services/transcription/transcription.service';
import { MarkdownModule } from 'ngx-markdown';

@Component({
  selector: 'analysis-detail',
  standalone: true,
  imports: [CommonModule, FormsModule, MarkdownModule],
  templateUrl: './analysis-detail.component.html',
  styleUrls: ['./analysis-detail.component.css']
})
export class AnalysisDetailComponent implements OnInit {
  transcription!: Transcription;
  editableContent: string = '';
  title = 'تحليل الجلسة';
  exporting: boolean = false; // Add exporting flag

  constructor(
    private route: ActivatedRoute,
    private service: TranscriptionService
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.service.getTranscriptionById(id).subscribe(data => {
      this.transcription = data;
      this.editableContent = data.Analyse || '';
    });
  }

  save(): void {
    const updated = { ...this.transcription, Analyse: this.editableContent };
    this.service.updateTranscription(this.transcription.id, updated).subscribe();
  }

  exportDocx(): void {
    this.exporting = true;
    this.service.exportAnalysisDocx(this.transcription.id).subscribe({
      next: blob => {
        this.download(blob, `${this.transcription.titreSceance}_analyse.docx`);
        this.exporting = false;
      },
      error: () => { this.exporting = false; }
    });
  }

  exportPdf(): void {
    this.exporting = true;
    this.service.exportAnalysisPdf(this.transcription.id).subscribe({
      next: blob => {
        this.download(blob, `${this.transcription.titreSceance}_analyse.pdf`);
        this.exporting = false;
      },
      error: () => { this.exporting = false; }
    });
  }

  private download(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  }
}
