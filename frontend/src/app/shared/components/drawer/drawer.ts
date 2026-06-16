import { Component, HostListener, input, output } from '@angular/core';
import { IconComponent } from '../icon/icon';

@Component({
  selector: 'app-drawer',
  imports: [IconComponent],
  templateUrl: './drawer.html',
  styleUrl: './drawer.css',
})
export class DrawerComponent {
  open = input(false);
  title = input('');
  subtitle = input('');

  closed = output<void>();

  close(): void {
    this.closed.emit();
  }

  @HostListener('document:keydown.escape')
  onEscapeKey(): void {
    if (this.open()) {
      this.close();
    }
  }
}
