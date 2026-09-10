import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import {
  AfterViewInit,
  Component,
  ElementRef,
  inject,
  OnDestroy,
  signal,
  ViewChild,
} from '@angular/core';
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

interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  opacity: number;
}

@Component({
  selector: 'app-chat',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css',
})
export class ChatComponent implements AfterViewInit, OnDestroy {
  @ViewChild('particleCanvas') private canvasRef!: ElementRef<HTMLCanvasElement>;

  private readonly http = inject(HttpClient);

  readonly question = signal('');
  readonly sending = signal(false);
  readonly error = signal('');
  readonly messages = signal<ChatMessage[]>([
    {
      role: 'assistant',
      content:
        'Welcome to MiB Support. Ask me about our services, policies, or product documentation.',
      grounded: true,
    },
  ]);

  readonly suggestions = [
    'What services does MiB Tech Solutions provide?',
    'How can I get help with my account?',
    'What is your support process?',
  ];

  // ─── Particle canvas ───────────────────────────────────────────────────────
  private particles: Particle[] = [];
  private animationFrameId = 0;
  private ctx!: CanvasRenderingContext2D;

  ngAfterViewInit(): void {
    this.initParticles();
  }

  ngOnDestroy(): void {
    cancelAnimationFrame(this.animationFrameId);
  }

  private initParticles(): void {
    const canvas = this.canvasRef.nativeElement;
    this.ctx = canvas.getContext('2d')!;

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resize();
    window.addEventListener('resize', resize);

    const count = Math.min(Math.floor((window.innerWidth * window.innerHeight) / 14000), 90);
    this.particles = Array.from({ length: count }, () => this.makeParticle(canvas));

    const animate = () => {
      this.animationFrameId = requestAnimationFrame(animate);
      this.drawParticles(canvas);
    };
    animate();
  }

  private makeParticle(canvas: HTMLCanvasElement): Particle {
    return {
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.35,
      vy: (Math.random() - 0.5) * 0.35,
      radius: Math.random() * 2 + 1,
      opacity: Math.random() * 0.5 + 0.15,
    };
  }

  private drawParticles(canvas: HTMLCanvasElement): void {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Connection lines
    for (let i = 0; i < this.particles.length; i++) {
      for (let j = i + 1; j < this.particles.length; j++) {
        const dx = this.particles[i].x - this.particles[j].x;
        const dy = this.particles[i].y - this.particles[j].y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const maxDist = 130;
        if (dist < maxDist) {
          ctx.beginPath();
          ctx.moveTo(this.particles[i].x, this.particles[i].y);
          ctx.lineTo(this.particles[j].x, this.particles[j].y);
          ctx.strokeStyle = `rgba(237,200,20,${0.12 * (1 - dist / maxDist)})`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }

    // Dots
    for (const p of this.particles) {
      p.x += p.vx;
      p.y += p.vy;

      // Wrap around edges
      if (p.x < 0) p.x = canvas.width;
      if (p.x > canvas.width) p.x = 0;
      if (p.y < 0) p.y = canvas.height;
      if (p.y > canvas.height) p.y = 0;

      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(237,200,20,${p.opacity})`;
      ctx.fill();
    }
  }

  // ─── Chat logic ────────────────────────────────────────────────────────────
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