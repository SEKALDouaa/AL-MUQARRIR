import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

@Component({
selector: 'app-pv-form',
standalone: true,
imports: [CommonModule, FormsModule],
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

onSubmit() {
    const dataToSend = {
      ...this.pv,
      Membres: this.pv.Membres.filter(m => m.trim() !== '').join(','),
      Absents: this.pv.Absents.filter(a => a.trim() !== '').join(',')
    };
    console.log(dataToSend);
    // TODO: envoyer `dataToSend` vers backend Flask
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
}
