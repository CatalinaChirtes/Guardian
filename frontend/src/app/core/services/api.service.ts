import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';
import { environment } from '../../../environments/environment';
import {
  TutorSession,
  SessionDetail,
  Exercise,
  CurriculumDocument,
} from '../models/interfaces';

@Injectable({ providedIn: 'root' })
export class ApiService {
  private baseUrl = environment.apiUrl;

  private http = inject(HttpClient);
  private auth = inject(AuthService);

  readonly sessions = signal<TutorSession[]>([]);
  private sessionsLoaded = false;
  private localSessionIds = new Set<string>();
  readonly documentCount = signal(0);
  private docsLoaded = false;

  addLocalSession(session: TutorSession): void {
    this.localSessionIds.add(session.id);
    this.sessions.update(s => [session, ...s.filter(x => x.id !== session.id)]);
  }

  refreshSessions(): void {
    this.listSessions().subscribe({
      next: (serverSessions) => {
        const serverIds = new Set(serverSessions.map(s => s.id));
        const kept = this.sessions().filter(s => this.localSessionIds.has(s.id) && !serverIds.has(s.id));
        this.localSessionIds.forEach(id => { if (serverIds.has(id)) this.localSessionIds.delete(id); });
        this.sessions.set([...kept, ...serverSessions]);
        this.sessionsLoaded = true;
      },
      error: () => {},
    });
  }

  refreshSessionsIfNeeded(): void {
    if (!this.sessionsLoaded) {
      this.refreshSessions();
    }
  }

  refreshDocumentCount(): void {
    this.listCurriculum().subscribe({
      next: (docs) => {
        this.documentCount.set(docs.length);
        this.docsLoaded = true;
      },
      error: () => {},
    });
  }

  refreshDocumentCountIfNeeded(): void {
    if (!this.docsLoaded) {
      this.refreshDocumentCount();
    }
  }

  clearCache(): void {
    this.sessions.set([]);
    this.sessionsLoaded = false;
    this.localSessionIds.clear();
    this.documentCount.set(0);
    this.docsLoaded = false;
  }

  private headers(): HttpHeaders {
    return new HttpHeaders({
      Authorization: `Bearer ${this.auth.accessToken()}`,
    });
  }

  // sessions
  createSession(
    exerciseId?: string,
    llmProvider = 'gemini'
  ): Observable<TutorSession> {
    return this.http.post<TutorSession>(
      `${this.baseUrl}/sessions`,
      { exercise_id: exerciseId, llm_provider: llmProvider },
      { headers: this.headers() }
    );
  }

  listSessions(): Observable<TutorSession[]> {
    return this.http.get<TutorSession[]>(`${this.baseUrl}/sessions`, {
      headers: this.headers(),
    });
  }

  getSession(id: string): Observable<SessionDetail> {
    return this.http.get<SessionDetail>(`${this.baseUrl}/sessions/${id}`, {
      headers: this.headers(),
    });
  }

  // exercises
  getRandomExercise(difficulty = 'Any'): Observable<Exercise> {
    const params = new HttpParams().set('difficulty', difficulty);
    return this.http.get<Exercise>(`${this.baseUrl}/exercises/random`, {
      headers: this.headers(),
      params,
    });
  }

  getExercise(id: string): Observable<Exercise> {
    return this.http.get<Exercise>(`${this.baseUrl}/exercises/${id}`, {
      headers: this.headers(),
    });
  }

  listExercises(
    difficulty = 'Any',
    limit = 10,
    offset = 0,
    shuffle = true
  ): Observable<Exercise[]> {
    const params = new HttpParams()
      .set('difficulty', difficulty)
      .set('limit', limit)
      .set('offset', offset)
      .set('shuffle', shuffle);
    return this.http.get<Exercise[]>(`${this.baseUrl}/exercises`, {
      headers: this.headers(),
      params,
    });
  }

  countExercises(difficulty = 'Any'): Observable<{ total: number }> {
    const params = new HttpParams().set('difficulty', difficulty);
    return this.http.get<{ total: number }>(`${this.baseUrl}/exercises/count`, {
      headers: this.headers(),
      params,
    });
  }

  // curriculum
  uploadCurriculum(file: File): Observable<CurriculumDocument> {
    const formData = new FormData();
    formData.append('file', file);
    return this.http.post<CurriculumDocument>(
      `${this.baseUrl}/curriculum/upload`,
      formData,
      { headers: this.headers() }
    );
  }

  listCurriculum(): Observable<CurriculumDocument[]> {
    return this.http.get<CurriculumDocument[]>(`${this.baseUrl}/curriculum`, {
      headers: this.headers(),
    });
  }

  deleteCurriculum(docId: string): Observable<void> {
    return this.http.delete<void>(`${this.baseUrl}/curriculum/${docId}`, {
      headers: this.headers(),
    });
  }

  // feedback
  submitFeedback(
    sessionId: string,
    messageId: string,
    feedbackType: string,
    value?: string
  ): Observable<{ id: string }> {
    return this.http.post<{ id: string }>(
      `${this.baseUrl}/feedback`,
      {
        session_id: sessionId,
        message_id: messageId,
        feedback_type: feedbackType,
        value,
      },
      { headers: this.headers() }
    );
  }
}
