import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
import { TranscriptionService } from '../../services/transcription/transcription.service';
import { HttpClientModule } from '@angular/common/http';

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

constructor(private transcriptionService: TranscriptionService) {}

  private formatTimeToHHMMSS(timeStr: string): string {
    // If time is already in HH:MM:SS format, return it as is
    if (timeStr.length === 8) return timeStr;

    // If time is in HH:MM format, add ":00" seconds part
    if (timeStr.length === 5) return `${timeStr}:00`;

    // Otherwise, just return original (backend should handle errors)
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
      next: () => alert('Transcription enregistrée avec succès!'),
      error: (err) => {
        console.error(err);
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
