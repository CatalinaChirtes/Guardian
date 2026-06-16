import { Component, inject, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { AuthLayoutComponent } from '../auth-layout/auth-layout';
import { IconComponent } from '../../../shared/components/icon/icon';
import { AuthFieldComponent } from '../../../shared/components/auth-field/auth-field';

@Component({
  selector: 'app-register',
  imports: [FormsModule, RouterLink, AuthLayoutComponent, NgClass, IconComponent, AuthFieldComponent],
  templateUrl: './register.html',
  styleUrl: './register.css',
})
export class RegisterComponent {
  email = '';
  password = '';
  confirmPassword = '';
  error = signal('');
  success = signal(false);
  loading = signal(false);
  showPassword = signal(false);
  showConfirm = signal(false);

  private emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;

  private auth = inject(AuthService);
  private attempts = 0;
  private lockedUntil = 0;

  async onRegister() {
    this.error.set('');
    this.success.set(false);

    const now = Date.now();
    if (now < this.lockedUntil) {
      const seconds = Math.ceil((this.lockedUntil - now) / 1000);
      this.error.set(`Too many attempts. Try again in ${seconds}s`);
      return;
    }

    if (!this.emailRegex.test(this.email)) {
      this.error.set('Please enter a valid email address');
      return;
    }
    if (this.password.length < 8) {
      this.error.set('Password must be at least 8 characters');
      return;
    }
    if (this.password !== this.confirmPassword) {
      this.error.set('Passwords do not match');
      return;
    }

    this.loading.set(true);
    const pwd = this.password;
    this.password = '';
    this.confirmPassword = '';
    const err = await this.auth.register(this.email, pwd);
    this.loading.set(false);

    this.attempts++;
    if (this.attempts >= 5) {
      this.lockedUntil = Date.now() + 60000;
      this.attempts = 0;
    }

    if (err) {
      this.error.set(err);
    } else {
      this.success.set(true);
    }
  }
}
