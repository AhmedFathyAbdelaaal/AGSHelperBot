import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-voice-logs',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './voice-logs.component.html'
})
export class VoiceLogsComponent implements OnInit {
  logs: any[] = [];
  loading = true;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<any[]>('/api/vclogs').subscribe({
      next: (data) => {
        this.logs = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error fetching VC logs', error);
        this.loading = false;
      }
    });
  }
}
