import { Component, DestroyRef, inject, signal, OnInit, OnDestroy, PLATFORM_ID } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { NgClass, isPlatformBrowser } from '@angular/common';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { environment } from '../../../environments/environment';
import { SidebarLayoutComponent } from '../../shared/components/sidebar-layout/sidebar-layout';
import { DrawerComponent } from '../../shared/components/drawer/drawer';
import { TopBarComponent } from './top-bar/top-bar';
import { CodeEditorComponent } from './code-editor/code-editor';
import { ChatPanelComponent } from './chat-panel/chat-panel';
import { DocPanelComponent } from './doc-panel/doc-panel';
import { ApiService } from '../../core/services/api.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { ChatMessage } from '../../core/models/interfaces';

@Component({
  selector: 'app-workspace',
  imports: [
    NgClass,
    SidebarLayoutComponent,
    DrawerComponent,
    TopBarComponent,
    CodeEditorComponent,
    ChatPanelComponent,
    DocPanelComponent,
  ],
  templateUrl: './workspace.html',
})
export class WorkspaceComponent implements OnInit, OnDestroy {
  api = inject(ApiService);
  private ws = inject(WebSocketService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);
  private destroyRef = inject(DestroyRef);
  private platformId = inject(PLATFORM_ID);

  auth = inject(AuthService);

  llmProvider = signal(isPlatformBrowser(this.platformId) ? (localStorage.getItem('llmProvider') || 'gemini') : 'gemini');
  language = signal('python');
  sessionId = signal('');
  starterCode = signal('');
  restoredCode = signal<string | null>(null);
  exerciseId = signal<string | null>(null);
  exerciseQuestion = signal<string | null>(null);
  exerciseDifficulty = signal<string | null>(null);
  currentCode = signal('');
  initialLoading = signal(true);

  historyMessages = signal<ChatMessage[]>([]);
  editorOpen = signal(false);
  splitMode = signal(true);
  docsOpen = signal(false);

  ngOnInit() {
    this.api.refreshSessionsIfNeeded();
    this.api.refreshDocumentCountIfNeeded();

    this.route.paramMap
      .pipe(takeUntilDestroyed(this.destroyRef))
      .subscribe((params) => {
        const routeId = params.get('id');
        if (routeId) {
          this.openSession(routeId, false);
        } else {
          const exerciseId = this.route.snapshot.queryParamMap.get('exerciseId');
          if (exerciseId) {
            this.loadExerciseById(exerciseId);
          } else {
            this.createNewSession();
          }
        }
      });
  }

  ngOnDestroy() {
    this.ws.disconnect();
  }

  onCodeChange(code: string) {
    this.currentCode.set(code);
  }

  startNewChat() {
    this.ws.disconnect();
    this.clearExerciseState();
    this.historyMessages.set([]);
    this.restoredCode.set('');
    this.currentCode.set('');
    this.editorOpen.set(false);
    this.createNewSession();
  }

  onProviderChange(provider: string) {
    this.llmProvider.set(provider);
    if (isPlatformBrowser(this.platformId)) {
      localStorage.setItem('llmProvider', provider);
    }
    this.ws.disconnect();
    this.historyMessages.set([]);
    this.createNewSession(this.exerciseId() ?? undefined);
  }

  openEditorPanel() {
    this.editorOpen.set(true);
    this.splitMode.set(true);
  }

  closeEditorPanel() {
    this.editorOpen.set(false);
    this.splitMode.set(true);
  }

  onSplitModeChange(split: boolean) {
    this.splitMode.set(split);
  }

  toggleDocs() {
    this.docsOpen.update((v) => !v);
  }

  closeDocs() {
    this.docsOpen.set(false);
  }

  closeChallenge() {
    this.clearExerciseState();
    this.editorOpen.set(false);
    this.startNewChat();
  }

  resumeSession(sessionId: string) {
    if (sessionId === this.sessionId()) return;

    this.ws.disconnect();
    this.clearExerciseState();
    this.currentCode.set('');
    this.historyMessages.set([]);
    this.restoredCode.set('');
    this.editorOpen.set(false);
    this.openSession(sessionId);
  }

  onDocumentCountChange(count: number) {
    this.api.documentCount.set(count);
  }

  onStartRandomChallenge() {
    this.api.getRandomExercise().subscribe({
      next: (ex) => {
        this.ws.disconnect();
        this.clearExerciseState();
        this.exerciseId.set(ex.id);
        this.exerciseQuestion.set(ex.question);
        this.exerciseDifficulty.set(ex.difficulty);
        this.starterCode.set(ex.starter_code);
        this.editorOpen.set(true);
        this.splitMode.set(true);
        this.historyMessages.set([]);
        this.createNewSession(ex.id);
      },
      error: (err) => { if (!environment.production) console.error('Failed to load random challenge', err); },
    });
  }

  private openSession(id: string, navigateUrl = true) {
    if (id === this.sessionId()) return;

    this.initialLoading.set(true);

    if (navigateUrl) {
      this.router.navigate(['/workspace', id], { replaceUrl: true });
    }

    this.api.getSession(id).subscribe({
      next: (detail) => {
        this.sessionId.set(detail.id);
        this.llmProvider.set(detail.llm_provider);
        if (isPlatformBrowser(this.platformId)) {
          localStorage.setItem('llmProvider', detail.llm_provider);
        }
        this.ws.connect(detail.id);

        if (detail.last_language) {
          this.language.set(detail.last_language);
        }

        this.historyMessages.set(detail.messages);

        if (detail.exercise_id) {
          this.exerciseId.set(detail.exercise_id);
          this.editorOpen.set(true);
          this.api.getExercise(detail.exercise_id).subscribe({
            next: (ex) => {
              this.exerciseQuestion.set(ex.question);
              this.exerciseDifficulty.set(ex.difficulty);
              this.starterCode.set(ex.starter_code);
              this.restoredCode.set(detail.last_code || ex.starter_code);
              this.currentCode.set(detail.last_code || ex.starter_code);
            },
            error: (err) => { if (!environment.production) console.error('Failed to load exercise for session', err); },
          });
        } else if (detail.last_code) {
          this.restoredCode.set(detail.last_code);
          this.currentCode.set(detail.last_code);
          this.editorOpen.set(true);
        }

        this.initialLoading.set(false);
      },
      error: () => {
        this.createNewSession();
      },
    });
  }

  private loadExerciseById(exerciseId: string) {
    this.api.getExercise(exerciseId).subscribe({
      next: (ex) => {
        this.exerciseId.set(ex.id);
        this.exerciseQuestion.set(ex.question);
        this.exerciseDifficulty.set(ex.difficulty);
        this.starterCode.set(ex.starter_code);
        this.editorOpen.set(true);
        this.createNewSession(ex.id);
      },
      error: () => {
        this.createNewSession();
      },
    });
  }

  private creatingSession = false;

  private createNewSession(exerciseId?: string) {
    if (this.creatingSession) return;
    this.creatingSession = true;
    this.api.createSession(exerciseId, this.llmProvider()).subscribe({
      next: (session) => {
        this.creatingSession = false;
        this.sessionId.set(session.id);
        this.ws.connect(session.id);
        this.initialLoading.set(false);
        this.router.navigate(['/workspace', session.id], {
          replaceUrl: true,
        });
      },
      error: () => {
        this.creatingSession = false;
        this.initialLoading.set(false);
      },
    });
  }

  private clearExerciseState() {
    this.exerciseId.set(null);
    this.exerciseQuestion.set(null);
    this.exerciseDifficulty.set(null);
    this.starterCode.set('');
  }

}
