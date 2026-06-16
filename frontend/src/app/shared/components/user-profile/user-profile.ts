import { Component, computed, inject, input, output } from '@angular/core';
import { AuthService } from '../../../core/services/auth.service';
import { AvatarComponent } from '../avatar/avatar';
import { ThemeToggleComponent } from '../theme-toggle/theme-toggle';
import { IconComponent } from '../icon/icon';
import { emailToDisplayName } from '../../../core/utils/format-name';

@Component({
  selector: 'app-user-profile',
  imports: [AvatarComponent, ThemeToggleComponent, IconComponent],
  templateUrl: './user-profile.html',
  styleUrl: './user-profile.css',
})
export class UserProfileComponent {
  collapsed = input(false);
  logout = output<void>();

  auth = inject(AuthService);

  userName = computed(() => emailToDisplayName(this.auth.userEmail() || ''));
}
