import { Component, input, output } from '@angular/core';
import { NgClass, NgTemplateOutlet } from '@angular/common';
import { LlmProviderPillComponent } from '../../../shared/components/llm-provider-pill/llm-provider-pill';
import { IconComponent } from '../../../shared/components/icon/icon';

@Component({
  selector: 'app-top-bar',
  imports: [NgClass, NgTemplateOutlet, LlmProviderPillComponent, IconComponent],
  templateUrl: './top-bar.html',
  styleUrl: './top-bar.css',
})
export class TopBarComponent {
  provider = input('gemini');
  editorOpen = input(false);
  splitMode = input(true);
  exerciseId = input<string | null>(null);
  mobileMode = input(false);

  providerChange = output<string>();
  openEditor = output<void>();
  closeEditor = output<void>();
  splitModeChange = output<boolean>();
  closeSession = output<void>();
}
