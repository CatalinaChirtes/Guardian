import { Component, input, output } from '@angular/core';
import { NgClass } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { IconComponent } from '../icon/icon';

@Component({
  selector: 'app-chat-input-bar',
  templateUrl: './chat-input-bar.html',
  styleUrl: './chat-input-bar.css',
  imports: [NgClass, FormsModule, IconComponent],
})
export class ChatInputBarComponent {
  disabled = input(false);
  codeAttached = input(false);

  messageSent = output<string>();
  attachCodeToggled = output<void>();

  inputText = '';

  send(): void {
    const text = this.inputText.trim();
    if (text) {
      this.messageSent.emit(text);
      this.inputText = '';
    }
  }

  toggleCode(): void {
    this.attachCodeToggled.emit();
  }
}
