import { Component, inject, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../core/services/auth.service';
import { AuthLayoutComponent } from '../auth-layout/auth-layout';
import { IconComponent } from '../../../shared/components/icon/icon';
import { AuthFieldComponent } from '../../../shared/components/auth-field/auth-field';

@Component({
  selector: 'app-reset-password',
  imports: [FormsModule, RouterLink, AuthLayoutComponent, NgClass, IconComponent, AuthFieldComponent],
  templateUrl: './reset-password.html',
  styleUrl: './reset-password.css',
})
export class ResetPasswordComponent {
  password = '';
  confirmPassword = '';
  error = signal('');
  loading = signal(false);
  success = signal(false);
  showPassword = signal(false);
  showConfirm = signal(false);

  private auth = inject(AuthService);
  private router = inject(Router);

  async onSubmit() {
    this.error.set('');

    if (this.password.length < 8) {
      this.error.set('Password must be at least 8 characters');
      return;
    }
    if (this.password !== this.confirmPassword) {
      this.error.set('Passwords do not match');
      return;
    }

    this.loading.set(true);
    const err = await this.auth.updatePassword(this.password);
    this.loading.set(false);

    if (err) {
      this.error.set(err);
    } else {
      this.success.set(true);
      this.password = '';
      this.confirmPassword = '';
      setTimeout(() => this.router.navigate(['/workspace']), 3000);
    }
  }
}
