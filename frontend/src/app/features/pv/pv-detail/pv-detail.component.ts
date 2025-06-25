import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Transcription } from '../../../models/transcription.model';
import { TranscriptionService } from '../../../services/transcription/transcription.service';
import { MarkdownModule } from 'ngx-markdown';

@Component({
selector: 'pv-detail',
standalone: true,
imports: [CommonModule, MarkdownModule, FormsModule],
templateUrl: './pv-detail.component.html',
styleUrls: ['./pv-detail.component.css']
})
export class PvDetailComponent implements OnInit {
transcription!: Transcription;
editableContent: string = '';
title = 'Pv';

constructor(
    private route: ActivatedRoute,
    private service: TranscriptionService
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.service.getTranscriptionById(id).subscribe(data => {
      this.transcription = data;
      this.editableContent = data.PV || '';
    });
  }

  save(): void {
    const updated = { ...this.transcription, PV: this.editableContent };
    this.service.updateTranscription(this.transcription.id, updated).subscribe();
  }

  exportDocx(): void {
    this.service.exportPvDocx(this.transcription.id).subscribe(blob => {
      this.download(blob, `${this.transcription.titreSceance}_pv.docx`);
    });
  }

  exportPdf(): void {
    this.service.exportPvPdf(this.transcription.id).subscribe(blob => {
      this.download(blob, `${this.transcription.titreSceance}_pv.pdf`);
    });
  }

  // Safely parse the transcription JSON or array
  parseTranscription(transcription: any): { speaker: string, text: string }[] {
    if (!transcription) return [];
    try {
      if (typeof transcription === 'string') {
        const parsed = JSON.parse(transcription);
        return Array.isArray(parsed) ? parsed : [];
      }
      if (Array.isArray(transcription)) {
        return transcription;
      }
      return [];
    } catch {
      return [];
    }
  }

  private download(blob: Blob, filename: string): void {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
  }
}
