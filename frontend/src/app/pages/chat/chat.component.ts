import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { Component, ElementRef, OnInit, ViewChild, effect, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { marked } from 'marked';

interface RAGSource {
  chunk_id: number;
  document_id: number;
  document_name: string;
  chunk_index: number;
  metadata: Record<string, unknown> | null;
  similarity_score: number;
}

interface ChatMessageResponse {
  answer: string;
  grounded: boolean;
  sources: RAGSource[];
  session_id: string;
  conversation_id: number;
}

interface EscalateResponse {
  escalated: boolean;
  session_id: string;
  message: string;
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
export class ChatComponent implements OnInit {
  private readonly http = inject(HttpClient);

  @ViewChild('scrollContainer') private scrollContainer?: ElementRef<HTMLDivElement>;

  readonly question = signal('');
  readonly sending = signal(false);
  readonly error = signal('');
  readonly escalated = signal(false);
  readonly sessionReady = signal(false);

  private sessionId = '';

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
    'Do you offer free consultations?',
    'What is your support and SLA process?',
  ];

  constructor() {
    effect(() => {
      this.messages();
      this.sending();
      setTimeout(() => this.scrollToBottom(), 40);
    });
  }

  ngOnInit(): void {
    // Create a conversation session on load
    this.http.post<{ session_id: string; conversation_id: number }>('/api/chat/conversations', {}).subscribe({
      next: (res) => {
        this.sessionId = res.session_id;
        this.sessionReady.set(true);
      },
      error: () => {
        // Session creation failed — the chat will still show but messages won't persist
        this.sessionReady.set(true);
      },
    });
  }

  scrollToBottom(): void {
    if (this.scrollContainer?.nativeElement) {
      const el = this.scrollContainer.nativeElement;
      el.scrollTo({ top: el.scrollHeight, behavior: 'smooth' });
    }
  }

  renderMarkdown(content: string): string {
    return marked.parse(content, { async: false }) as string;
  }

  escalateToHuman(): void {
    if (this.escalated()) return;

    if (this.sessionId) {
      this.http
        .post<EscalateResponse>(`/api/chat/conversations/${this.sessionId}/escalate`, {})
        .subscribe({
          next: (res) => {
            this.escalated.set(true);
            this.messages.update((msgs) => [
              ...msgs,
              { role: 'assistant', content: res.message, grounded: true },
            ]);
          },
          error: () => {
            this.error.set('We could not reach a support agent. Please try again.');
          },
        });
    } else {
      this.escalated.set(true);
      this.messages.update((msgs) => [
        ...msgs,
        {
          role: 'assistant',
          content:
            'Please contact support@mibtechsolutions.com so a representative can assist you.',
          grounded: true,
        },
      ]);
    }
  }

  sendQuestion(): void {
    const value = this.question().trim();
    if (!value || this.sending()) return;

    this.messages.update((messages) => [...messages, { role: 'user', content: value }]);
    this.question.set('');
    this.error.set('');
    this.sending.set(true);

    const url = this.sessionId
      ? `/api/chat/conversations/${this.sessionId}/messages`
      : '/api/rag/answer';

    const payload = this.sessionId ? { message: value } : { question: value };

    this.http.post<ChatMessageResponse>(url, payload).subscribe({
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