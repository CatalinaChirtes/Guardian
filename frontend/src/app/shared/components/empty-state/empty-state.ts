import { Component, input } from '@angular/core';
import { IconComponent } from '../icon/icon';

@Component({
  selector: 'app-empty-state',
  imports: [IconComponent],
  templateUrl: './empty-state.html',
  styleUrl: './empty-state.css',
})
export class EmptyStateComponent {
  icon = input.required<string>();
  title = input.required<string>();
  subtitle = input.required<string>();
}
