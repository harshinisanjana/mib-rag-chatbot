import { Routes } from '@angular/router';
import { HomeComponent } from './pages/home/home.component';
import { PlaceholderComponent } from './pages/placeholder/placeholder.component';

export const routes: Routes = [
  { path: '', component: HomeComponent },
  {
    path: 'chat',
    component: PlaceholderComponent,
    data: {
      title: 'Customer Chat',
      description: 'Chat interface will be implemented in Phase 9.',
    },
  },
  {
    path: 'admin',
    component: PlaceholderComponent,
    data: {
      title: 'Admin Portal',
      description: 'Document management and analytics will be implemented in Phase 11.',
    },
  },
  {
    path: 'agent',
    component: PlaceholderComponent,
    data: {
      title: 'Support Agent',
      description: 'Escalation management will be implemented in Phase 10.',
    },
  },
  { path: '**', redirectTo: '' },
];
