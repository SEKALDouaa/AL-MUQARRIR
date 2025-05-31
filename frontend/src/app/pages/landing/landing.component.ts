import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

import {HeroComponent} from './hero/hero.component'
import {CallToActionComponent} from './call-to-action/call-to-action.component'

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [HeroComponent, CallToActionComponent, CommonModule],
  templateUrl: './landing.component.html',
  styleUrl: './landing.component.css'
})
export class LandingComponent {

}
