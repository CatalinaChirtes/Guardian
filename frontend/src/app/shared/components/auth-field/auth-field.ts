import { Component, HostListener, input, signal } from '@angular/core';
import { NgClass } from '@angular/common';
import { IconComponent } from '../icon/icon';

@Component({
  selector: 'app-auth-field',
  imports: [NgClass, IconComponent],
  templateUrl: './auth-field.html',
  styleUrl: './auth-field.css',
})
export class AuthFieldComponent {
  label = input.required<string>();
  icon = input.required<string>();
  fieldId = input.required<string>();

  focused = signal(false);

  @HostListener('focusin')
  onFocusIn() { this.focused.set(true); }

  @HostListener('focusout')
  onFocusOut() { this.focused.set(false); }
}
