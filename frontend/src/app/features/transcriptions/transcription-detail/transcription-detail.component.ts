import { Component, OnInit } from '@angular/core';
import { ActivatedRoute } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Transcription } from '../../../models/transcription.model';
import { TranscriptionService } from '../../../services/transcription/transcription.service';

@Component({
selector: 'transcription-detail',
standalone: true,
imports: [CommonModule, FormsModule],
templateUrl: './transcription-detail.component.html',
styleUrls: ['./transcription-detail.component.css']
})
export class TranscriptionDetailComponent implements OnInit {
transcription!: Transcription;
editableContent: string = '';
title = 'Transcription';

constructor(
    private route: ActivatedRoute,
    private service: TranscriptionService
  ) {}

  ngOnInit(): void {
    const id = Number(this.route.snapshot.paramMap.get('id'));
    this.service.getTranscriptionById(id).subscribe(data => {
      this.transcription = data;
      this.editableContent = data.Transcription || '';
    });
  }

  save(): void {
    const updated = { ...this.transcription, PV: this.editableContent };
    this.service.updateTranscription(this.transcription.id, updated).subscribe();
  }
}
