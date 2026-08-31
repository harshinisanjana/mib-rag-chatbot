import { Component, inject, OnInit, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

interface HealthResponse {
  status: string;
  service: string;
  version: string;
}

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './home.component.html',
  styleUrl: './home.component.css',
})
export class HomeComponent implements OnInit {
  private readonly http = inject(HttpClient);

  readonly backendStatus = signal<'loading' | 'healthy' | 'error'>('loading');
  readonly backendInfo = signal<HealthResponse | null>(null);

  ngOnInit(): void {
    this.http.get<HealthResponse>('/health').subscribe({
      next: (response) => {
        this.backendInfo.set(response);
        this.backendStatus.set('healthy');
      },
      error: () => {
        this.backendStatus.set('error');
      },
    });
  }
}
