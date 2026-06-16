import { Component, effect, input, output, signal } from '@angular/core';
import {
  CdkDragDrop,
  CdkDrag,
  CdkDropList,
  moveItemInArray,
} from '@angular/cdk/drag-drop';
import { IconComponent } from '../../../../shared/components/icon/icon';

@Component({
  selector: 'app-parsons-puzzle',
  imports: [CdkDropList, CdkDrag, IconComponent],
  templateUrl: './parsons-puzzle.html',
  styleUrl: './parsons-puzzle.css',
})
export class ParsonsPuzzleComponent {
  lines = input.required<string[]>();
  submitOrder = output<string[]>();

  orderedLines = signal<string[]>([]);
  result = signal<'correct' | 'incorrect' | ''>('');
  private startTime = Date.now();

  constructor() {
    effect(() => {
      this.orderedLines.set([...this.lines()]);
      this.startTime = Date.now();
      this.result.set('');
    });
  }

  drop(event: CdkDragDrop<string[]>) {
    const items = [...this.orderedLines()];
    moveItemInArray(items, event.previousIndex, event.currentIndex);
    this.orderedLines.set(items);
    this.result.set('');
  }

  onSubmit() {
    this.submitOrder.emit(this.orderedLines());
  }

  setResult(correct: boolean) {
    this.result.set(correct ? 'correct' : 'incorrect');
  }

  getTimeSpent(): number {
    return Math.round((Date.now() - this.startTime) / 1000);
  }
}
