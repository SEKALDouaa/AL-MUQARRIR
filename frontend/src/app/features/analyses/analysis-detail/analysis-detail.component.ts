import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Transcription } from '../../../models/transcription.model';
import { TranscriptionService } from '../../../services/transcription/transcription.service';

@Component({
selector: 'analysis-detail',
standalone: true,
imports: [CommonModule, FormsModule],
templateUrl: './analysis-detail.component.html',
styleUrls: ['./analysis-detail.component.css']
})
export class AnalysisDetailComponent implements OnInit {
transcription!: Transcription;
editableContent: string = '';
title = 'تحليل الجلسة';

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
    this.service.exportAnalysisDocx(this.transcription.id).subscribe(blob => {
      this.download(blob, `${this.transcription.titreSceance}_analyse.docx`);
    });
  }

  exportPdf(): void {
    this.service.exportAnalysisPdf(this.transcription.id).subscribe(blob => {
      this.download(blob, `${this.transcription.titreSceance}_analyse.pdf`);
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
