import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms'; // 👈
import { CommonModule } from '@angular/common'; // 👈

@Component({
selector: 'app-pv-form',
standalone: true, // 👈
imports: [CommonModule, FormsModule], // 👈 très important
templateUrl: './pv-form.component.html',
styleUrls: ['./pv-form.component.css']
})
export class PvFormComponent {
pv = {
titre: '',
date: '',
participants: '',
ordreDuJour: ''
};

onSubmit() {
    console.log(this.pv);
  }
}
