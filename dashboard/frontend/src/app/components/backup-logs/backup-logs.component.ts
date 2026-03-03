import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-backup-logs',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './backup-logs.component.html'
})
export class BackupLogsComponent implements OnInit {
  logs: any[] = [];
  loading = true;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<any[]>('/api/backuplogs').subscribe({
      next: (data) => {
        this.logs = data || []; // Handle null/empty
        this.loading = false;
      },
      error: (error) => {
        console.error('Error fetching Backup logs', error);
        this.loading = false;
      }
    });
  }
}
