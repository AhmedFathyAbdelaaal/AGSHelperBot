import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-requests',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './requests.component.html'
})
export class RequestsComponent implements OnInit {
  requests: any[] = [];
  filteredRequests: any[] = [];
  loading = true;
  activeTab = 'All'; // 'All', 'Feature', 'Idea', 'Bug'

  selectedRequest: any = null;

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.http.get<any[]>('/api/requests').subscribe({
      next: (data) => {
        this.requests = data;
        this.filterRequests();
        this.loading = false;
      },
      error: (error) => {
        console.error('Error fetching requests', error);
        this.loading = false;
      }
    });
  }

  setTab(tab: string) {
    this.activeTab = tab;
    this.filterRequests();
  }

  filterRequests() {
    if (this.activeTab === 'All') {
      this.filteredRequests = this.requests;
    } else {
      this.filteredRequests = this.requests.filter(r => r.req_type === this.activeTab);
    }
  }

  openModal(request: any) {
    this.selectedRequest = request;
  }

  closeModal() {
    this.selectedRequest = null;
  }

  // Helpers for displaying data based on type
  getLabel(key: string, type: string): string {
    const labels: any = {
      'Bug': {
        'data_1': 'Platform',
        'data_2': 'Severity',
        'data_3': 'Steps to Reproduce',
        'data_4': 'Expected vs Actual',
        'data_5': 'Additional Info'
      },
      'Idea': {
        'data_1': 'Category',
        'data_2': 'Description',
        'data_3': 'Why it helps',
        'data_4': 'Visual Reference',
        'data_5': 'Additional Info'
      },
      'Feature': {
        'data_1': 'Use Case',
        'data_2': 'Functionality',
        'data_3': 'Priority',
        'data_4': 'Impact',
        'data_5': 'Additional Info'
      }
    };
    return labels[type]?.[key] || key;
  }
}
