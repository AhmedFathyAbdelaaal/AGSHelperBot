import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-user-status',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './user-status.component.html'
})
export class UserStatusComponent implements OnInit {
  statuses: any[] = [];
  loading = true;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<any[]>('/api/status').subscribe({
      next: (data) => {
        this.statuses = data;
        this.loading = false;
      },
      error: (error) => {
        console.error('Error fetching statuses', error);
        this.loading = false;
      }
    });
  }
}
