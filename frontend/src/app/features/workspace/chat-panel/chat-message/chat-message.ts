import { Component, input, output, computed, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { ChatMessage } from '../../../../core/models/interfaces';
import { BadgeComponent } from '../../../../shared/components/badge/badge';
import { IconComponent } from '../../../../shared/components/icon/icon';
import { MarkdownPipe } from '../../../../shared/pipes/markdown.pipe';

@Component({
  selector: 'app-chat-message',
  imports: [NgClass, BadgeComponent, IconComponent, MarkdownPipe],
  templateUrl: './chat-message.html',
  styleUrl: './chat-message.css',
})
export class ChatMessageComponent {
  msg = input.required<ChatMessage>();
  feedback = output<{ messageId: string; type: string }>();

  private _localFeedback = signal<'thumbs_up' | 'thumbs_down' | null>(null);

  activeFeedback = computed(() => {
    const local = this._localFeedback();
    if (local !== null) return local;
    const fb = this.msg().feedback;
    if (fb === 'thumbs_up' || fb === 'thumbs_down') return fb;
    return null;
  });

  onFeedback(type: 'thumbs_up' | 'thumbs_down') {
    this._localFeedback.set(type);
    this.feedback.emit({ messageId: this.msg().id, type });
  }
}
