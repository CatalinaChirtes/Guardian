import { Component, computed, input, output, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { IconComponent } from '../icon/icon';
import { DropdownComponent } from '../dropdown/dropdown';

@Component({
  selector: 'app-llm-provider-pill',
  imports: [NgClass, IconComponent, DropdownComponent],
  templateUrl: './llm-provider-pill.html',
  styleUrl: './llm-provider-pill.css',
})
export class LlmProviderPillComponent {
  provider = input('gemini');
  providerChange = output<string>();

  private logoMap: Record<string, string> = {
    'gemini': 'assets/images/Google_Gemini_logo.svg',
    'openai': 'assets/images/ChatGPT_logo.svg',
    'anthropic': 'assets/images/Claude_logo.svg',
    'ollama-qwen': 'assets/images/Ollama_logo.svg',
    'ollama-gemma': 'assets/images/Ollama_logo.svg',
  };

  providerLogo = computed(() => this.logoMap[this.provider()] || 'assets/images/orb-logo.svg');
  providerDarkInvert = computed(() => ['openai', 'ollama-qwen', 'ollama-gemma'].includes(this.provider()));

  displayName = computed(() => {
    const map: Record<string, string> = {
      'gemini': 'Gemini 2.5 Flash',
      'openai': 'GPT-5.4 Mini',
      'anthropic': 'Claude Haiku 4.5',
      'ollama-qwen': 'Qwen 2.5 3B',
      'ollama-gemma': 'Gemma 3 4B',
    };
    return map[this.provider()] || this.provider();
  });

  isLocal = computed(() => this.provider().startsWith('ollama'));

  dropdownOpen = signal(false);

  providers = [
    { value: 'gemini', label: 'Gemini 2.5 Flash', local: false, hint: 'Google', logo: 'assets/images/Google_Gemini_logo.svg', darkInvert: false },
    { value: 'openai', label: 'GPT-5.4 Mini', local: false, hint: 'OpenAI', logo: 'assets/images/ChatGPT_logo.svg', darkInvert: true },
    { value: 'anthropic', label: 'Claude Haiku 4.5', local: false, hint: 'Anthropic', logo: 'assets/images/Claude_logo.svg', darkInvert: false },
    { value: 'ollama-qwen', label: 'Qwen 2.5 3B', local: true, hint: 'Local', logo: 'assets/images/Ollama_logo.svg', darkInvert: true },
    { value: 'ollama-gemma', label: 'Gemma 3 4B', local: true, hint: 'Local', logo: 'assets/images/Ollama_logo.svg', darkInvert: true },
  ];

  selectProvider(value: string): void {
    this.providerChange.emit(value);
    this.dropdownOpen.set(false);
  }
}
