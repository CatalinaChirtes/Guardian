import { Injectable, Injector, inject, signal, computed, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Router } from '@angular/router';
import { createClient, SupabaseClient, Session } from '@supabase/supabase-js';
import { environment } from '../../../environments/environment';
import { firstValueFrom } from 'rxjs';
import { WebSocketService } from './websocket.service';
import { ApiService } from './api.service';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private supabase: SupabaseClient;
  private sessionSignal = signal<Session | null>(null);
  private _ready: Promise<void>;

  readonly isAuthenticated = computed(() => !!this.sessionSignal());
  readonly accessToken = computed(() => this.sessionSignal()?.access_token ?? '');
  readonly userId = computed(() => this.sessionSignal()?.user?.id ?? '');
  readonly userEmail = computed(() => this.sessionSignal()?.user?.email ?? '');

  private platformId = inject(PLATFORM_ID);
  private router = inject(Router);
  private http = inject(HttpClient);
  private injector = inject(Injector);

  constructor() {
    this.supabase = createClient(
      environment.supabaseUrl,
      environment.supabaseAnonKey,
      { auth: { persistSession: true, autoRefreshToken: true, storage: globalThis.sessionStorage } }
    );

    this._ready = this.supabase.auth.getSession().then(({ data }) => {
      this.sessionSignal.set(data.session);
    });

    this.supabase.auth.onAuthStateChange((_event, session) => {
      this.sessionSignal.set(session);
    });
  }

  ready(): Promise<void> {
    return this._ready;
  }

  async register(email: string, password: string): Promise<string | null> {
    try {
      await firstValueFrom(
        this.http.post(`${environment.apiUrl}/auth/register`, { email, password })
      );
      return null;
    } catch (err: unknown) {
      if (err instanceof HttpErrorResponse) {
        return err.error?.detail ?? 'Registration failed';
      }
      return 'Registration failed';
    }
  }

  async login(email: string, password: string): Promise<string | null> {
    const { error } = await this.supabase.auth.signInWithPassword({
      email,
      password,
    });
    return error ? error.message : null;
  }

  async resetPassword(email: string): Promise<string | null> {
    const redirectTo = isPlatformBrowser(this.platformId)
      ? `${window.location.origin}/reset-password`
      : '/reset-password';
    const { error } = await this.supabase.auth.resetPasswordForEmail(email, {
      redirectTo,
    });
    return error ? error.message : null;
  }

  async updatePassword(newPassword: string): Promise<string | null> {
    const { error } = await this.supabase.auth.updateUser({
      password: newPassword,
    });
    return error ? error.message : null;
  }

  async logout(): Promise<void> {
    this.injector.get(WebSocketService).disconnect();
    this.injector.get(ApiService).clearCache();

    await this.supabase.auth.signOut();
    this.router.navigate(['/login']);
  }
}
