import { Component, computed, input } from '@angular/core';

const SIZE_MAP: Record<'sm' | 'md' | 'lg', number> = {
  sm: 28,
  md: 34,
  lg: 42,
};

@Component({
  selector: 'app-avatar',
  templateUrl: './avatar.html',
  styleUrl: './avatar.css',
})
export class AvatarComponent {
  name = input('');
  size = input<'sm' | 'md' | 'lg'>('md');

  initials = computed(() => {
    const raw = this.name().trim();
    if (!raw) {
      return '?';
    }

    // if it looks like an email, use the part before @
    const identifier = raw.includes('@') ? raw.split('@')[0] : raw;

    const parts = identifier
      .replace(/[._-]/g, ' ')
      .trim()
      .split(/\s+/)
      .filter(Boolean);

    if (parts.length === 0) {
      return '?';
    }

    if (parts.length === 1) {
      return parts[0].charAt(0).toUpperCase();
    }

    return (parts[0].charAt(0) + parts[parts.length - 1].charAt(0)).toUpperCase();
  });

  avatarStyle = computed(() => {
    const px = SIZE_MAP[this.size()];
    return {
      width: `${px}px`,
      height: `${px}px`,
      'border-radius': '10px',
      'font-size': `${px * 0.4}px`,
      'font-weight': '700',
      display: 'grid',
      'place-items': 'center',
      color: 'var(--accent-strong)',
      background: 'var(--accent-soft)',
      border: '1px solid color-mix(in srgb, var(--accent) 22%, transparent)',
      'user-select': 'none',
    };
  });
}
