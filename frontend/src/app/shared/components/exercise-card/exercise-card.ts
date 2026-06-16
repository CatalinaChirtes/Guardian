import { Component, input, output } from '@angular/core';
import { Exercise } from '../../../core/models/interfaces';
import { BadgeComponent } from '../badge/badge';
import { IconComponent } from '../icon/icon';
import { MarkdownPipe } from '../../pipes/markdown.pipe';

@Component({
  selector: 'app-exercise-card',
  imports: [BadgeComponent, IconComponent, MarkdownPipe],
  templateUrl: './exercise-card.html',
  styleUrl: './exercise-card.css',
})
export class ExerciseCardComponent {
  exercise = input.required<Exercise>();
  status = input<'solved' | 'started' | null>(null);

  cardClicked = output<Exercise>();
  continueClicked = output<Exercise>();

  onCardClick() {
    this.cardClicked.emit(this.exercise());
  }

  onContinue(event: MouseEvent) {
    event.stopPropagation();
    this.continueClicked.emit(this.exercise());
  }
}
