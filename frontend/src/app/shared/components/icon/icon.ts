import { Component, effect, inject, input, signal, PLATFORM_ID } from '@angular/core';
import { isPlatformBrowser } from '@angular/common';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import DOMPurify from 'dompurify';

const cache = new Map<string, string>();
const pending = new Map<string, Promise<string>>();

function cleanSvg(raw: string): string {
  const sanitized = DOMPurify.sanitize(raw, { USE_PROFILES: { svg: true, svgFilters: true } });
  return sanitized
    .replace(/\s+width="[^"]*"/, ' width="100%"')
    .replace(/\s+height="[^"]*"/, ' height="100%"')
    .replace(/stroke="black"/g, 'stroke="currentColor"')
    .replace(/fill="black"/g, 'fill="currentColor"');
}

@Component({
  selector: 'app-icon',
  templateUrl: './icon.html',
  styleUrl: './icon.css',
})
export class IconComponent {
  name = input.required<string>();
  size = input(16);

  private sanitizer = inject(DomSanitizer);
  private platformId = inject(PLATFORM_ID);

  svg = signal<SafeHtml>('');

  constructor() {
    effect(() => {
      const iconName = this.name();
      if (!iconName || !isPlatformBrowser(this.platformId)) return;
      if (!/^[a-z0-9-]+$/.test(iconName)) return;

      const cached = cache.get(iconName);
      if (cached) {
        this.svg.set(this.sanitizer.bypassSecurityTrustHtml(cached));
        return;
      }

      const req = pending.get(iconName);
      if (req) {
        req.then(s => this.svg.set(this.sanitizer.bypassSecurityTrustHtml(s)));
        return;
      }

      const p = fetch(`/assets/icons/${iconName}.svg`)
        .then(r => {
          if (!r.ok) throw new Error('fetch failed');
          return r.text();
        })
        .then(raw => {
          const cleaned = cleanSvg(raw);
          cache.set(iconName, cleaned);
          pending.delete(iconName);
          return cleaned;
        })
        .catch(() => {
          pending.delete(iconName);
          return '';
        });

      pending.set(iconName, p);
      p.then(s => this.svg.set(this.sanitizer.bypassSecurityTrustHtml(s)));
    });
  }
}
