import { Routes } from '@angular/router';
import { authGuard } from './core/guards/auth.guard';
import { guestGuard } from './core/guards/guest.guard';

export const routes: Routes = [
  { path: 'login', canActivate: [guestGuard], loadComponent: () => import('./features/auth/login/login').then(m => m.LoginComponent) },
  { path: 'register', canActivate: [guestGuard], loadComponent: () => import('./features/auth/register/register').then(m => m.RegisterComponent) },
  { path: 'forgot-password', canActivate: [guestGuard], loadComponent: () => import('./features/auth/forgot-password/forgot-password').then(m => m.ForgotPasswordComponent) },
  { path: 'reset-password', loadComponent: () => import('./features/auth/reset-password/reset-password').then(m => m.ResetPasswordComponent) },
  {
    path: 'workspace',
    canActivate: [authGuard],
    loadComponent: () => import('./features/workspace/workspace').then(m => m.WorkspaceComponent),
  },
  {
    path: 'workspace/:id',
    canActivate: [authGuard],
    loadComponent: () => import('./features/workspace/workspace').then(m => m.WorkspaceComponent),
  },
  {
    path: 'practice',
    canActivate: [authGuard],
    loadComponent: () => import('./features/practice/practice').then(m => m.PracticeComponent),
  },
  { path: '', redirectTo: 'workspace', pathMatch: 'full' },
  { path: '**', redirectTo: 'workspace' },
];
