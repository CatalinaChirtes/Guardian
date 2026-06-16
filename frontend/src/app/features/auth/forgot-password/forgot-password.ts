import { Component, inject, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { AuthLayoutComponent } from '../auth-layout/auth-layout';
import { IconComponent } from '../../../shared/components/icon/icon';
import { AuthFieldComponent } from '../../../shared/components/auth-field/auth-field';

@Component({
  selector: 'app-forgot-password',
  imports: [FormsModule, RouterLink, AuthLayoutComponent, NgClass, IconComponent, AuthFieldComponent],
  templateUrl: './forgot-password.html',
  styleUrl: './forgot-password.css',
})
export class ForgotPasswordComponent {
  email = '';
  error = signal('');
  loading = signal(false);
  sent = signal(false);
  private auth = inject(AuthService);
  private attempts = 0;
  private lockedUntil = 0;

  async onSubmit() {
    this.error.set('');

    const now = Date.now();
    if (now < this.lockedUntil) {
      const seconds = Math.ceil((this.lockedUntil - now) / 1000);
      this.error.set(`Too many attempts. Try again in ${seconds}s`);
      return;
    }

    if (!this.email.trim()) {
      this.error.set('Please enter your email');
      return;
    }
    this.loading.set(true);
    const err = await this.auth.resetPassword(this.email);
    this.loading.set(false);

    this.attempts++;
    if (this.attempts >= 5) {
      this.lockedUntil = Date.now() + 60000;
      this.attempts = 0;
    }

    if (err) {
      this.error.set(err);
    } else {
      this.sent.set(true);
    }
  }
}
