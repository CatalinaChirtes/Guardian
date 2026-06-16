import { Component, inject, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { AuthLayoutComponent } from '../auth-layout/auth-layout';
import { IconComponent } from '../../../shared/components/icon/icon';
import { AuthFieldComponent } from '../../../shared/components/auth-field/auth-field';

@Component({
  selector: 'app-login',
  imports: [FormsModule, RouterLink, AuthLayoutComponent, NgClass, IconComponent, AuthFieldComponent],
  templateUrl: './login.html',
  styleUrl: './login.css',
})
export class LoginComponent {
  email = '';
  password = '';
  error = signal('');
  loading = signal(false);
  showPassword = signal(false);
  passwordFocused = signal(false);

  private auth = inject(AuthService);
  private router = inject(Router);
  private attempts = 0;
  private lockedUntil = 0;

  async onLogin() {
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
    if (!this.password) {
      this.error.set('Please enter your password');
      return;
    }
    this.loading.set(true);
    const pwd = this.password;
    this.password = '';
    const err = await this.auth.login(this.email, pwd);
    this.loading.set(false);

    this.attempts++;
    if (this.attempts >= 5) {
      this.lockedUntil = Date.now() + 60000;
      this.attempts = 0;
    }

    if (err) {
      this.error.set(err);
    } else {
      this.router.navigate(['/workspace']);
    }
  }
}
