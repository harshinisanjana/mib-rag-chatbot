import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, ViewChild, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

interface RAGSource {
  chunk_id: number;
  document_id: number;
  chunk_index: number;
  metadata: Record<string, unknown> | null;
  similarity_score: number;
}

interface RAGResponse {
  answer: string;
  grounded: boolean;
  sources: RAGSource[];
}

interface ChatMessage {
  role: 'assistant' | 'user';
  content: string;
  sources?: RAGSource[];
  grounded?: boolean;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css',
})
export class ChatComponent {
  private readonly http = inject(HttpClient);

  @ViewChild('scrollContainer') private scrollContainer?: ElementRef<HTMLDivElement>;

  readonly question = signal('');
  readonly sending = signal(false);
  readonly error = signal('');
  readonly escalated = signal(false);
  readonly messages = signal<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Hello! Welcome to MiB Support. How can we help you today? You can ask about our enterprise software, cloud architectures, AI integrations, or service offerings.',
      grounded: true,
    },
  ]);

  readonly suggestions = [
    'What services does MiB Tech Solutions provide?',
    'How can I get help with my account or deployment?',
    'What is your support and SLA process?',
  ];

  constructor() {
    effect(() => {
      // Re-run whenever messages or sending status update
      this.messages();
      this.sending();
      setTimeout(() => this.scrollToBottom(), 40);
    });
  }

  scrollToBottom(): void {
    if (this.scrollContainer?.nativeElement) {
      const el = this.scrollContainer.nativeElement;
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }

  escalateToHuman(): void {
    if (this.escalated()) {
      return;
    }
    this.escalated.set(true);
    this.messages.update((msgs) => [
      ...msgs,
      {
        role: 'assistant',
        content:
          'Your conversation has been routed to our tier-2 customer support team. A representative will connect with you here shortly, or reach out to your registered email. You can also contact us directly at support@mibtechsolutions.com.',
        grounded: true,
      },
    ]);
  }

  sendQuestion(): void {
    const value = this.question().trim();
    if (!value || this.sending()) {
      return;
    }

    this.messages.update((messages) => [...messages, { role: 'user', content: value }]);
    this.question.set('');
    this.error.set('');
    this.sending.set(true);

    this.http.post<RAGResponse>('/api/rag/answer', { question: value }).subscribe({
      next: (response) => {
        this.messages.update((messages) => [
          ...messages,
          {
            role: 'assistant',
            content: response.answer,
            grounded: response.grounded,
            sources: response.sources,
          },
        ]);
        this.sending.set(false);
      },
      error: () => {
        this.error.set('The support service is temporarily unavailable. Please try again.');
        this.sending.set(false);
      },
    });
  }

  useSuggestion(suggestion: string): void {
    this.question.set(suggestion);
    this.sendQuestion();
  }
}