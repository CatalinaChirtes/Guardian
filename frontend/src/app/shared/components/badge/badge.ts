import { Component, computed, input } from '@angular/core';

export type BadgeVariant =
  | 'default'
  | 'lav'
  | 'success'
  | 'solved'
  | 'warning'
  | 'interview'
  | 'danger'
  | 'competition'
  | 'info'
  | 'introductory'
  | 'theory'
  | 'socratic'
  | 'puzzle'
  | 'cloud'
  | 'local'
  | 'emerald'
  | 'amber'
  | 'rose'
  | 'blue'
  | 'gray';

interface ColorDef {
  fg: string;
  bg: string;
  border: string;
}

const COLORS: Record<string, ColorDef> = {
  lav: {
    fg: 'var(--accent-strong)',
    bg: 'var(--accent-soft)',
    border: 'color-mix(in srgb, var(--accent) 26%, transparent)',
  },
  emerald: {
    fg: 'var(--emerald)',
    bg: 'var(--emerald-soft)',
    border: 'color-mix(in srgb, var(--emerald) 30%, transparent)',
  },
  amber: {
    fg: 'var(--amber)',
    bg: 'var(--amber-soft)',
    border: 'color-mix(in srgb, var(--amber) 30%, transparent)',
  },
  rose: {
    fg: 'var(--rose)',
    bg: 'var(--rose-soft)',
    border: 'color-mix(in srgb, var(--rose) 30%, transparent)',
  },
  blue: {
    fg: 'var(--blue)',
    bg: 'var(--blue-soft)',
    border: 'color-mix(in srgb, var(--blue) 30%, transparent)',
  },
  gray: {
    fg: 'var(--text-2)',
    bg: 'var(--surface-2)',
    border: 'var(--border-strong)',
  },
};

const VARIANT_MAP: Record<string, string> = {
  default: 'lav',
  lav: 'lav',
  socratic: 'lav',
  cloud: 'lav',
  emerald: 'emerald',
  success: 'emerald',
  solved: 'emerald',
  theory: 'emerald',
  introductory: 'emerald',
  info: 'emerald',
  amber: 'amber',
  warning: 'amber',
  interview: 'amber',
  puzzle: 'amber',
  rose: 'rose',
  danger: 'rose',
  competition: 'rose',
  blue: 'blue',
  gray: 'gray',
  local: 'gray',
};

@Component({
  selector: 'app-badge',
  templateUrl: './badge.html',
  styleUrl: './badge.css',
})
export class BadgeComponent {
  label = input('');
  variant = input<BadgeVariant | string>('default');
  solid = input(false);
  icon = input<string | undefined>(undefined);

  badgeStyle = computed<Record<string, string>>(() => {
    const key = VARIANT_MAP[this.variant()] ?? 'lav';
    const c = COLORS[key];

    const base: Record<string, string> = {
      'padding': '3px 9px',
      'border-radius': '99px',
      'font-size': '11.5px',
      'font-weight': '600',
      'letter-spacing': '.01em',
      'line-height': '1.4',
      'white-space': 'nowrap',
      'display': 'inline-flex',
      'align-items': 'center',
      'gap': '5px',
    };

    if (this.solid()) {
      return {
        ...base,
        'color': '#fff',
        'background': c.fg,
      };
    }

    return {
      ...base,
      'color': c.fg,
      'background': c.bg,
      'border': `1px solid ${c.border}`,
    };
  });
}
