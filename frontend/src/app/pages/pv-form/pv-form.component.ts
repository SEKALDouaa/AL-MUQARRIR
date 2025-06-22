import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { TranscriptionService } from '../../services/transcription/transcription.service';
import { HttpClientModule } from '@angular/common/http';
import { Router } from '@angular/router';
import { Transcription } from '../../models/transcription.model'; // Import the model

@Component({
  selector: 'app-pv-form',
  standalone: true,
  imports: [CommonModule, FormsModule, HttpClientModule],
  templateUrl: './pv-form.component.html',
  styleUrls: ['./pv-form.component.css']
})
export class PvFormComponent {
  pv = {
    titreSceance: '',
    dateSceance: '',
    HeureDebut: '',
    HeureFin: '',
    President: '',
    Secretaire: '',
    Membres: [''],
    Absents: [''],
    OrdreDuJour: '',
    DateRedaction: '',
    DateProchaineReunion: ''
  };

  constructor(
    private transcriptionService: TranscriptionService,
    private router: Router
  ) {}

  private formatTimeToHHMMSS(timeStr: string): string {
    if (timeStr.length === 8) return timeStr;
    if (timeStr.length === 5) return `${timeStr}:00`;
    return timeStr;
  }

  onSubmit() {
    const dataToSend = {
      ...this.pv,
      Membres: this.pv.Membres.filter(m => m.trim() !== '').join(','),
      Absents: this.pv.Absents.filter(a => a.trim() !== '').join(','),
      HeureDebut: this.formatTimeToHHMMSS(this.pv.HeureDebut),
      HeureFin: this.formatTimeToHHMMSS(this.pv.HeureFin)
    };

    this.transcriptionService.createTranscription(dataToSend).subscribe({
      next: (newPv: Transcription) => {
        // The backend returns the created PV object with its ID.
        if (newPv && newPv.id) {
          this.router.navigate(['/transcription-mode', newPv.id, 'select-transcription-mode']);
        } else {
          console.error('PV created, but no ID was returned from the backend.');
          alert('PV created, but failed to get ID for next step.');
        }
      },
      error: (err) => {
        console.error('Erreur lors de l’enregistrement:', err);
        alert('Erreur lors de l’enregistrement.');
      }
    });
  }

  addMembre() {
    this.pv.Membres.push('');
  }

  removeMembre(index: number) {
    this.pv.Membres.splice(index, 1);
  }

  addAbsent() {
    this.pv.Absents.push('');
  }

  removeAbsent(index: number) {
    this.pv.Absents.splice(index, 1);
  }

  trackByIndex(index: number): number {
    return index;
  }
}
