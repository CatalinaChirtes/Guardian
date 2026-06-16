import { Component, computed, inject, input, output, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { IconComponent } from '../icon/icon';
import { UserProfileComponent } from '../user-profile/user-profile';

@Component({
  selector: 'app-sidebar-layout',
  imports: [NgClass, RouterLink, RouterLinkActive, IconComponent, UserProfileComponent],
  templateUrl: './sidebar-layout.html',
  styleUrl: './sidebar-layout.css',
})
export class SidebarLayoutComponent {
  // inputs for dynamic content
  sessions = input<Array<{
    id: string;
    title: string | null;
    session_type: string;
    exercise_id: string | null;
    solved: boolean;
  }>>([]);
  activeSessionId = input('');
  documentCount = input(0);

  // outputs for user actions
  newChat = output<void>();
  sessionSelected = output<string>();
  documentsClicked = output<void>();
  logout = output<void>();

  // services
  auth = inject(AuthService);
  private router = inject(Router);

  chatActive = computed(() => {
    const id = this.activeSessionId();
    return !!id && !this.sessions().some(s => s.id === id);
  });

  // responsive state
  sidebarCollapsed = signal(false);
  mobileMenuOpen = signal(false);

  toggleSidebar() {
    this.sidebarCollapsed.update(v => !v);
  }

  onSessionClick(sessionId: string) {
    this.sessionSelected.emit(sessionId);
    this.mobileMenuOpen.set(false);
  }

  onChatClick() {
    if (this.chatActive()) return;
    this.newChat.emit();
    this.mobileMenuOpen.set(false);
  }

  onNewChat() {
    this.newChat.emit();
    this.mobileMenuOpen.set(false);
  }

  onLogout() {
    this.logout.emit();
  }
}
