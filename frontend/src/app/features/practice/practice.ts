import { Component, computed, DestroyRef, inject, signal, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router } from '@angular/router';
import { NgClass } from '@angular/common';
import { forkJoin } from 'rxjs';
import { SidebarLayoutComponent } from '../../shared/components/sidebar-layout/sidebar-layout';
import { BadgeComponent } from '../../shared/components/badge/badge';
import { ModalComponent } from '../../shared/components/modal/modal';
import { DrawerComponent } from '../../shared/components/drawer/drawer';
import { DocPanelComponent } from '../workspace/doc-panel/doc-panel';
import { IconComponent } from '../../shared/components/icon/icon';
import { ExerciseCardComponent } from '../../shared/components/exercise-card/exercise-card';
import { EmptyStateComponent } from '../../shared/components/empty-state/empty-state';
import { DropdownComponent } from '../../shared/components/dropdown/dropdown';
import { MarkdownPipe } from '../../shared/pipes/markdown.pipe';
import { ApiService } from '../../core/services/api.service';
import { Exercise, TutorSession } from '../../core/models/interfaces';
import { AuthService } from '../../core/services/auth.service';

type Tab = 'all' | 'started' | 'solved';
type BrowseMode = 'random' | 'browse';

@Component({
  selector: 'app-practice',
  imports: [NgClass, SidebarLayoutComponent, BadgeComponent, ModalComponent, DrawerComponent, DocPanelComponent, IconComponent, ExerciseCardComponent, EmptyStateComponent, DropdownComponent, MarkdownPipe],
  templateUrl: './practice.html',
  styleUrl: './practice.css',
})
export class PracticeComponent implements OnInit {
  exercises = signal<Exercise[]>([]);
  challengeSessions = signal<TutorSession[]>([]);
  docsOpen = signal(false);
  loading = signal(false);
  selectedExercise = signal<Exercise | null>(null);
  activeTab = signal<Tab>('all');
  browseMode = signal<BrowseMode>('random');
  difficulty = signal('Any');
  diffDropdownOpen = signal(false);
  limit = 10;

  difficultyOptions: { value: string; label: string; dot: string }[] = [
    { value: 'Any', label: 'Any difficulty', dot: '' },
    { value: 'introductory', label: 'Introductory', dot: 'var(--emerald)' },
    { value: 'interview', label: 'Interview', dot: 'var(--amber)' },
    { value: 'competition', label: 'Competition', dot: 'var(--rose)' },
  ];

  difficultyLabel = computed(() => this.difficultyOptions.find(o => o.value === this.difficulty())?.label || 'Any difficulty');

  readonly tabs: { key: Tab; label: string; countSignal?: () => Exercise[] }[] = [
    { key: 'all', label: 'All' },
    { key: 'started', label: 'In progress', countSignal: () => this.startedExercises() },
    { key: 'solved', label: 'Solved', countSignal: () => this.solvedExercises() },
  ];

  selectDifficulty(value: string) {
    this.difficulty.set(value);
    this.diffDropdownOpen.set(false);
    this.onDifficultyChange();
  }

  offset = signal(0);
  totalCount = signal(0);

  currentPage = computed(() => Math.floor(this.offset() / this.limit) + 1);
  totalPages = computed(() => Math.ceil(this.totalCount() / this.limit));

  sessionMap = computed(() => {
    const map = new Map<string, TutorSession>();
    for (const s of this.challengeSessions()) {
      if (s.exercise_id) {
        const existing = map.get(s.exercise_id);
        if (!existing || s.solved) {
          map.set(s.exercise_id, s);
        }
      }
    }
    return map;
  });

  startedExercises = signal<Exercise[]>([]);
  solvedExercises = signal<Exercise[]>([]);

  api = inject(ApiService);
  auth = inject(AuthService);
  private router = inject(Router);
  private destroyRef = inject(DestroyRef);

  ngOnInit() {
    this.loadExercises();
    this.loadAllSessions();
    this.api.refreshDocumentCountIfNeeded();
  }

  loadExercises() {
    this.loading.set(true);
    const shuffle = this.browseMode() === 'random';
    const off = shuffle ? 0 : this.offset();
    this.api.listExercises(this.difficulty(), this.limit, off, shuffle).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (data) => {
        this.exercises.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  private loadAllSessions() {
    this.api.listSessions().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (sessions) => {
        this.api.sessions.set(sessions);
        const challenges = sessions.filter((s) => s.session_type === 'challenge' && s.exercise_id);
        this.challengeSessions.set(challenges);
        this.loadUserExercises(challenges);
      },
      error: () => {},
    });
  }

  private loadUserExercises(sessions: TutorSession[]) {
    const startedIds = new Set<string>();
    const solvedIds = new Set<string>();
    for (const s of sessions) {
      if (s.exercise_id) {
        if (s.solved) {
          solvedIds.add(s.exercise_id);
        } else {
          startedIds.add(s.exercise_id);
        }
      }
    }
    for (const id of solvedIds) {
      startedIds.delete(id);
    }

    if (startedIds.size > 0) {
      forkJoin([...startedIds].map((id) => this.api.getExercise(id))).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
        next: (results) => this.startedExercises.set(results),
        error: () => {},
      });
    }

    if (solvedIds.size > 0) {
      forkJoin([...solvedIds].map((id) => this.api.getExercise(id))).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
        next: (results) => this.solvedExercises.set(results),
        error: () => {},
      });
    }
  }

  setTab(tab: Tab) {
    this.activeTab.set(tab);
  }

  setBrowseMode(mode: BrowseMode) {
    if (mode === this.browseMode()) return;
    this.browseMode.set(mode);
    this.offset.set(0);
    if (mode === 'browse') {
      this.loadCount();
    }
    this.loadExercises();
  }

  onDifficultyChange() {
    this.offset.set(0);
    if (this.browseMode() === 'browse') {
      this.loadCount();
    }
    this.loadExercises();
  }

  private loadCount() {
    this.api.countExercises(this.difficulty()).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (res) => this.totalCount.set(res.total),
      error: () => {},
    });
  }

  nextPage() {
    this.offset.update((v) => v + this.limit);
    this.loadExercises();
  }

  prevPage() {
    this.offset.update((v) => Math.max(0, v - this.limit));
    this.loadExercises();
  }

  refresh() {
    this.loadExercises();
  }

  getStatus(exerciseId: string): 'solved' | 'started' | null {
    const session = this.sessionMap().get(exerciseId);
    if (!session) return null;
    return session.solved ? 'solved' : 'started';
  }

  openDetail(ex: Exercise) {
    this.selectedExercise.set(ex);
    this.api.getExercise(ex.id).pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (full) => this.selectedExercise.set(full),
      error: () => {},
    });
  }

  closeDetail() {
    this.selectedExercise.set(null);
  }

  startExercise(ex: Exercise) {
    this.selectedExercise.set(null);
    this.router.navigate(['/workspace'], {
      queryParams: { exerciseId: ex.id },
    });
  }

  continueExercise(ex: Exercise) {
    this.selectedExercise.set(null);
    const session = this.sessionMap().get(ex.id);
    if (session) {
      this.router.navigate(['/workspace', session.id]);
    } else {
      this.startExercise(ex);
    }
  }

  startNewChat() {
    this.router.navigate(['/workspace']);
  }

  resumeSession(sessionId: string) {
    this.router.navigate(['/workspace', sessionId]);
  }
}
