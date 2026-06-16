import { Injectable, inject, signal } from '@angular/core';
import { Subject } from 'rxjs';
import { AuthService } from './auth.service';
import { WsIncoming } from '../models/interfaces';
import { environment } from '../../../environments/environment';

@Injectable({ providedIn: 'root' })
export class WebSocketService {
  private ws: WebSocket | null = null;
  private sessionId = '';
  private connectGeneration = 0;
  private reconnectAttempts = 0;

  readonly connected = signal(false);
  readonly messages$ = new Subject<WsIncoming>();

  private auth = inject(AuthService);

  connect(sessionId: string): void {
    this.disconnect();
    this.sessionId = sessionId;
    const generation = ++this.connectGeneration;
    const token = this.auth.accessToken();
    if (!token) {
      console.warn('[ws] No auth token available, skipping connect');
      return;
    }
    const url = `${environment.wsUrl}/chat/${sessionId}`;
    this.ws = new WebSocket(url);

    this.ws.onopen = () => {
      if (generation !== this.connectGeneration) return;
      this.ws!.send(JSON.stringify({ type: 'auth', token }));
      this.reconnectAttempts = 0;
      this.connected.set(true);
    };

    this.ws.onmessage = (event) => {
      if (generation !== this.connectGeneration) return;
      try {
        const data = JSON.parse(event.data);
        if (typeof data === 'object' && data !== null && 'type' in data) {
          this.messages$.next(data as WsIncoming);
        }
      } catch {}
    };

    this.ws.onclose = () => {
      if (generation !== this.connectGeneration) return;
      this.connected.set(false);
      if (this.sessionId) {
        const delay = Math.min(3000 * Math.pow(2, this.reconnectAttempts), 30000);
        this.reconnectAttempts++;
        setTimeout(() => {
          if (this.sessionId && generation === this.connectGeneration) {
            this.connect(this.sessionId);
          }
        }, delay);
      }
    };

    this.ws.onerror = () => {
      if (generation !== this.connectGeneration) return;
      this.ws?.close();
    };
  }

  send(data: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }

  disconnect(): void {
    this.sessionId = '';
    this.connectGeneration++;
    this.reconnectAttempts = 0;
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN || this.ws.readyState === WebSocket.CLOSING) {
        this.ws.close();
      } else {
        const stale = this.ws;
        stale.onopen = stale.onmessage = stale.onclose = stale.onerror = null;
      }
      this.ws = null;
    }
    this.connected.set(false);
  }
}
