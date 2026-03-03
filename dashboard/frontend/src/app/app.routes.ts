import { Routes } from '@angular/router';
import { DashboardComponent } from './components/dashboard/dashboard.component';
import { UserStatusComponent } from './components/user-status/user-status.component';
import { VoiceLogsComponent } from './components/voice-logs/voice-logs.component';
import { RequestsComponent } from './components/requests/requests.component';
import { ReportsComponent } from './components/reports/reports.component';
import { BackupLogsComponent } from './components/backup-logs/backup-logs.component';

export const routes: Routes = [
  { path: '', component: DashboardComponent },
  { path: 'status', component: UserStatusComponent },
  { path: 'vclogs', component: VoiceLogsComponent },
  { path: 'requests', component: RequestsComponent },
  { path: 'reports', component: ReportsComponent },
  { path: 'backups', component: BackupLogsComponent },
  { path: '**', redirectTo: '' }
];
