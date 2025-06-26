import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { TranscriptionService } from '../../services/transcription/transcription.service';
import { Transcription } from '../../models/transcription.model';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
export class DashboardComponent implements OnInit {
  transcriptions: Transcription[] = [];
  kpis = {
    total: 0,
    pvs: 0,
    analyses: 0,
    upcomingMeeting: '',
    lastActivity: ''
  };
  recentPVs: Transcription[] = [];
  calendarEvents: { date: string, type: string }[] = [];

  currentMonth: number = new Date().getMonth();
  currentYear: number = new Date().getFullYear();
  daysInMonth: number[] = [];
  meetingDays: Set<number> = new Set();
  firstDayOfWeek: number = 0;
  emptyDays: any[] = [];

  constructor(private service: TranscriptionService, private router: Router) {}

  ngOnInit(): void {
    const today = new Date();
    this.service.getAllTranscriptions().subscribe(list => {
      this.transcriptions = list.sort((a, b) => b.dateSceance.localeCompare(a.dateSceance));
      this.kpis.total = list.length;
      this.kpis.pvs = list.length;
      this.kpis.analyses = list.length;
      if (list.length) {
        const latest = this.transcriptions[0];
        this.kpis.lastActivity = latest.dateSceance;
      }
      this.recentPVs = this.transcriptions.slice(0, 3);
      this.calendarEvents = this.transcriptions.flatMap(t => [
        { date: t.dateSceance, type: 'past' },
        ...(t.DateProchaineReunion ? [{ date: t.DateProchaineReunion, type: 'upcoming' }] : [])
      ]);

      // Preprocess upcoming meetings: find the next DateProchaineReunion after today
      const futureMeetings = this.transcriptions
        .map(t => t.DateProchaineReunion)
        .filter(dateStr => !!dateStr)
        .map(dateStr => new Date(dateStr!))
        .filter(date => date > today)
        .sort((a, b) => a.getTime() - b.getTime());
      this.kpis.upcomingMeeting = futureMeetings.length ? futureMeetings[0].toISOString().slice(0, 10) : 'Aucune';

      // Calendar logic
      const month = this.currentMonth + 1;
      this.daysInMonth = Array.from({length: new Date(this.currentYear, month, 0).getDate()}, (_, i) => i + 1);
      // Mark all meeting days in the current month for both dateSceance and DateProchaineReunion (if >= today)
      const todayDay = today.getDate();
      const todayMonth = today.getMonth();
      const todayYear = today.getFullYear();
      this.meetingDays = new Set([
        ...this.transcriptions
          .map(t => {
            const d = new Date(t.dateSceance);
            // Only color if in current month/year and >= today
            if (
              d.getMonth() === this.currentMonth &&
              d.getFullYear() === this.currentYear &&
              (d > today || (d.getDate() === todayDay && d.getMonth() === todayMonth && d.getFullYear() === todayYear))
            ) {
              return d.getDate();
            }
            return null;
          })
          .filter((d): d is number => d !== null),
        ...this.transcriptions
          .map(t => {
            if (!t.DateProchaineReunion) return null;
            const d = new Date(t.DateProchaineReunion);
            // Only color if in current month/year and >= today
            if (
              d.getMonth() === this.currentMonth &&
              d.getFullYear() === this.currentYear &&
              (d > today || (d.getDate() === todayDay && d.getMonth() === todayMonth && d.getFullYear() === todayYear))
            ) {
              return d.getDate();
            }
            return null;
          })
          .filter((d): d is number => d !== null)
      ]);
      // Calculate empty days for calendar grid
      const jsFirstDay = new Date(this.currentYear, this.currentMonth, 1).getDay();
      // Adjust for Monday as first day (jsFirstDay: 0=Sunday, 1=Monday...)
      this.firstDayOfWeek = jsFirstDay === 0 ? 6 : jsFirstDay - 1;
      this.emptyDays = Array(this.firstDayOfWeek).fill(0);
    });
  }

  goToPvForm() {
    this.router.navigate(['/Home/pv-form']);
  }

  goToPvDetail(id: number) {
    this.router.navigate(['/Home/pv-detail', id]);
  }

  goToPvList() {
    this.router.navigate(['/Home/pv-list']);
  }

  
  contactSupport() {
    window.location.href = 'mailto: AL-MUQARRIR&#64gmail.com';
  }

  goToDocumentation() {
    this.router.navigate(['/Home/documentation']);
  }
}
