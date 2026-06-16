import {
  Component,
  computed,
  inject,
  input,
  output,
  signal,
  effect,
  viewChild,
  ElementRef,
  afterNextRender,
  OnInit,
  OnDestroy,
} from '@angular/core';
import { ChatMessageComponent } from './chat-message/chat-message';
import { ParsonsPuzzleComponent } from './parsons-puzzle/parsons-puzzle';
import { BadgeComponent } from '../../../shared/components/badge/badge';
import { ChatInputBarComponent } from '../../../shared/components/chat-input-bar/chat-input-bar';
import { IconComponent } from '../../../shared/components/icon/icon';
import { MarkdownPipe } from '../../../shared/pipes/markdown.pipe';
import { ChatMessage, WsIncoming } from '../../../core/models/interfaces';
import { WebSocketService } from '../../../core/services/websocket.service';
import { ApiService } from '../../../core/services/api.service';
import { AuthService } from '../../../core/services/auth.service';
import { emailToDisplayName } from '../../../core/utils/format-name';
import { Subscription } from 'rxjs';

@Component({
  selector: 'app-chat-panel',
  imports: [ChatMessageComponent, ParsonsPuzzleComponent, BadgeComponent, ChatInputBarComponent, IconComponent, MarkdownPipe],
  templateUrl: './chat-panel.html',
  styleUrl: './chat-panel.css',
})
export class ChatPanelComponent implements OnInit, OnDestroy {
  sessionId = input.required<string>();
  currentCode = input('');
  exerciseQuestion = input<string | null>(null);
  exerciseDifficulty = input<string | null>(null);
  historyMessages = input<ChatMessage[]>([]);
  codeAttached = input(false);
  firstMessageSent = output<void>();
  attachCodeToggled = output<void>();
  startChallenge = output<void>();

  messages = signal<ChatMessage[]>([]);
  streamingContent = signal('');
  isWaiting = signal(false);
  puzzleLines = signal<string[] | null>(null);
  analysisMsg = signal('');
  ws = inject(WebSocketService);
  private api = inject(ApiService);
  auth = inject(AuthService);

  readonly quickActions = [
    { icon: 'bug', title: "I'm stuck on a bug", subtitle: 'Walk through my code with hints', message: "I'm stuck on a bug in my code. Can you help me debug it?" },
    { icon: 'highlighter', title: 'Explain a concept', subtitle: 'Grounded in my course notes', message: 'Can you explain recursion using my course notes?' },
    { icon: 'rocket-launch', title: 'Start a challenge', subtitle: 'Practice on a real problem', action: 'challenge' as const },
    { icon: 'compass', title: "Why won't my loop stop?", subtitle: 'Reason about termination', message: 'Help me fix an infinite loop in my code. Can you reason about termination?' },
  ];

  userName = computed(() => emailToDisplayName(this.auth.userEmail() || ''));

  showEmptyState = computed(() =>
    this.messages().length === 0 && !this.puzzleLines() && !this.exerciseQuestion()
  );

  private scrollContainer = viewChild<ElementRef>('scrollContainer');
  private puzzleComponent = viewChild(ParsonsPuzzleComponent);
  private sub: Subscription | null = null;

  constructor() {
    effect(() => {
      const history = this.historyMessages();
      this.messages.set(history);
      this.streamingContent.set('');
      this.analysisMsg.set('');
      this.restorePuzzleFromHistory(history);
      requestAnimationFrame(() => this.scrollToBottom());
    });

    afterNextRender(() => {
      this.scrollToBottom();
    });
  }

  ngOnInit() {
    this.sub = this.ws.messages$.subscribe((msg) => this.handleWsMessage(msg));
  }

  ngOnDestroy() {
    this.sub?.unsubscribe();
  }

  sendWithContent(content: string) {
    const isFirst = this.messages().length === 0;
    this.messages.update((m) => [...m, this.createMessage('student', content)]);
    if (isFirst) {
      const id = this.sessionId();
      if (!this.api.sessions().some(s => s.id === id)) {
        this.api.addLocalSession({
          id, user_id: '', session_type: 'chat', exercise_id: null,
          title: content.length > 50 ? content.substring(0, 50) + '...' : content,
          llm_provider: '', total_attempts: 0,
          puzzle_triggered: false, solved: false,
          created_at: new Date().toISOString(), ended_at: null,
        });
      }
      this.firstMessageSent.emit();
    }
    this.analysisMsg.set('');
    this.isWaiting.set(true);

    this.ws.send({
      type: 'message',
      content,
      code: this.currentCode(),
    });

    this.scrollToBottom();
  }

  onFeedback(event: { messageId: string; type: string }) {
    this.api
      .submitFeedback(this.sessionId(), event.messageId, event.type)
      .subscribe({ error: () => {} });
  }

  onPuzzleSubmit(order: string[]) {
    const puzzle = this.puzzleComponent();
    this.ws.send({
      type: 'puzzle_submit',
      student_order: order,
      time_spent_seconds: puzzle?.getTimeSpent() ?? 0,
    });
  }

  private handleWsMessage(msg: WsIncoming) {
    switch (msg.type) {
      case 'response': {
        this.isWaiting.set(false);
        this.streamingContent.set('');
        this.messages.update((m) => [...m, this.createMessage('tutor', msg.content ?? '', {
          id: msg.message_id ?? crypto.randomUUID(),
          mode: (msg.mode as ChatMessage['mode']) ?? null,
          sources: msg.sources ?? null,
        })]);
        this.api.refreshSessions();
        break;
      }
      case 'token':
        this.streamingContent.update((s) => s + (msg.content ?? ''));
        break;
      case 'done':
        this.streamingContent.set('');
        break;
      case 'puzzle':
        this.isWaiting.set(false);
        this.puzzleLines.set(msg.lines ?? null);
        if (msg.content) {
          this.messages.update((m) => [...m, this.createMessage('tutor', msg.content!, { mode: 'puzzle' })]);
        }
        break;
      case 'puzzle_result': {
        this.isWaiting.set(false);
        this.puzzleComponent()?.setResult(msg.is_correct ?? false);
        if (msg.is_correct) {
          this.puzzleLines.set(null);
        }
        this.messages.update((m) => [...m, this.createMessage('tutor',
          msg.message ?? (msg.is_correct ? 'Correct! Well done!' : 'Not quite right. Try again!'),
          { mode: 'puzzle', feedback: msg.is_correct ? 'correct' : 'incorrect' },
        )]);
        break;
      }
      case 'analysis':
        if (msg.errors && msg.errors.length > 0) {
          this.analysisMsg.set(`Syntax errors: ${msg.errors.map(e => {
            const str = typeof e === 'string' ? e : (e as any).msg ?? (e as any).message ?? JSON.stringify(e);
            return this.escapeHtml(str);
          }).join('; ')}`);
        } else if (msg.language) {
          this.analysisMsg.set(
            `Detected: ${msg.language} - ${msg.is_valid ? 'Valid' : 'Has issues'}`
          );
        }
        break;
      case 'error': {
        this.isWaiting.set(false);
        this.streamingContent.set('');
        const safeMessage = this.escapeHtml(msg.message ?? 'Unknown error');
        this.messages.update((m) => [...m, this.createMessage('tutor',
          `Sorry, I encountered an error. Please try again.\n\n_${safeMessage}_`,
          { mode: 'error' },
        )]);
        break;
      }
    }
    this.scrollToBottom();
  }

  private restorePuzzleFromHistory(messages: ChatMessage[]) {
    let lastPuzzleLines: string[] | null = null;
    let puzzleSolved = false;

    for (const msg of messages) {
      if (msg.mode === 'puzzle' && msg.sources) {
        try {
          const parsed = JSON.parse(msg.sources);
          if (Array.isArray(parsed) && parsed.every((item: unknown) => typeof item === 'string')) {
            lastPuzzleLines = parsed;
            puzzleSolved = false;
          }
        } catch {
          lastPuzzleLines = null;
        }
      }
      if (msg.mode === 'puzzle_result' && msg.feedback === 'correct') {
        puzzleSolved = true;
      }
    }

    this.puzzleLines.set(puzzleSolved ? null : lastPuzzleLines);
  }

  private scrollToBottom() {
    const el = this.scrollContainer()?.nativeElement;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }

  private escapeHtml(text: string): string {
    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  }

  private createMessage(role: 'student' | 'tutor', content: string, overrides: Partial<ChatMessage> = {}): ChatMessage {
    return {
      id: crypto.randomUUID(),
      session_id: this.sessionId(),
      role,
      content,
      mode: null,
      llm_provider: null,
      llm_model: null,
      latency_ms: null,
      sources: null,
      feedback: null,
      created_at: new Date().toISOString(),
      ...overrides,
    };
  }
}
