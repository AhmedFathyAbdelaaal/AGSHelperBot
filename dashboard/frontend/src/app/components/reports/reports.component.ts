import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-reports',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './reports.component.html'
})
export class ReportsComponent implements OnInit {
  reports: any[] = [];
  loading = true;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<any[]>('/api/reports').subscribe({
      next: (data) => {
        this.reports = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error fetching reports', error);
        this.loading = false;
      }
    });
  }
}
