import { Component, inject, OnInit, signal } from '@angular/core';
import { ActivatedRoute, RouterLink } from '@angular/router';

@Component({
  selector: 'app-placeholder',
  standalone: true,
  imports: [RouterLink],
  template: `
    <section class="placeholder">
      <h1>{{ title() }}</h1>
      <p>{{ description() }}</p>
      <a routerLink="/">Back to home</a>
    </section>
  `,
  styles: [`
    .placeholder {
      max-width: 640px;
      margin: 4rem auto;
      padding: 0 1.5rem;
      text-align: center;
    }

    h1 {
      margin-bottom: 0.75rem;
    }

    p {
      color: #475569;
      margin-bottom: 1.5rem;
    }

    a {
      color: #2563eb;
      text-decoration: none;
      font-weight: 600;
    }
  `],
})
export class PlaceholderComponent implements OnInit {
  private readonly route = inject(ActivatedRoute);

  readonly title = signal('');
  readonly description = signal('');

  ngOnInit(): void {
    const data = this.route.snapshot.data;
    this.title.set(data['title'] ?? 'Coming Soon');
    this.description.set(data['description'] ?? '');
  }
}
