import {
  Component,
  computed,
  input,
  output,
  effect,
  signal,
  ElementRef,
  viewChild,
  afterNextRender,
  OnDestroy,
  inject,
  PLATFORM_ID,
} from '@angular/core';
import { isPlatformBrowser, NgClass } from '@angular/common';
import { ThemeService } from '../../../core/services/theme.service';
import { IconComponent } from '../../../shared/components/icon/icon';
import { DropdownComponent } from '../../../shared/components/dropdown/dropdown';

declare const monaco: any;

const LANG_MAP: Record<string, string> = {
  python: 'python',
  javascript: 'javascript',
  java: 'java',
  cpp: 'cpp',
};

@Component({
  selector: 'app-code-editor',
  imports: [NgClass, IconComponent, DropdownComponent],
  templateUrl: './code-editor.html',
  styleUrl: './code-editor.css',
})
export class CodeEditorComponent implements OnDestroy {
  language = input('python');
  initialCode = input('');
  restoredCode = input<string | null>(null);
  languageChange = output<string>();
  codeChange = output<string>();
  closeEditor = output<void>();

  editorContainer = viewChild<ElementRef>('editorContainer');

  langDropdownOpen = signal(false);
  lineCount = signal(0);

  languages = [
    { value: 'python', label: 'Python' },
    { value: 'java', label: 'Java' },
    { value: 'cpp', label: 'C++' },
    { value: 'javascript', label: 'JavaScript' },
  ];

  langLabel = computed(() => this.languages.find(l => l.value === this.language())?.label ?? this.language());

  selectLanguage(value: string) {
    this.languageChange.emit(value);
    this.langDropdownOpen.set(false);
  }

  private editor: any = null;
  private themeService = inject(ThemeService);
  private platformId = inject(PLATFORM_ID);
  private isBrowser = isPlatformBrowser(this.platformId);
  private static monacoErrorSuppressed = false;

  constructor() {
    afterNextRender(() => {
      this.loadMonaco();
    });

    effect(() => {
      const code = this.restoredCode();
      if (this.editor && code !== null) {
        const current = this.editor.getValue();
        if (current !== code) {
          this.editor.setValue(code);
        }
      }
    });

    effect(() => {
      const lang = this.language();
      if (this.editor) {
        const model = this.editor.getModel();
        if (model) {
          monaco.editor.setModelLanguage(model, LANG_MAP[lang] || lang);
        }
      }
    });

    effect(() => {
      const theme = this.themeService.theme();
      if (this.editor) {
        monaco.editor.setTheme(theme === 'dark' ? 'guardian-dark' : 'guardian-light');
      }
    });
  }

  private loadMonaco() {
    if (!this.isBrowser) return;

    const onLoad = () => {
      (window as any).require.config({
        paths: { vs: 'vs' },
      });
      (window as any).require(['vs/editor/editor.main'], () => {
        this.initEditor();
      });
    };

    if ((window as any).require) {
      onLoad();
      return;
    }

    const script = document.createElement('script');
    script.src = 'vs/loader.js';
    script.onload = onLoad;
    script.onerror = () => {
      console.error('Failed to load Monaco Editor loader script');
    };
    document.head.appendChild(script);
  }

  private initEditor() {
    const container = this.editorContainer()?.nativeElement;
    if (!container) return;

    const theme = this.themeService.theme();
    const lang = this.language();
    const restored = this.restoredCode();
    const initial = (restored !== null ? restored : this.initialCode()) || '';

    monaco.editor.defineTheme('guardian-dark', {
      base: 'vs-dark',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#160e20',
        'editor.lineHighlightBackground': '#1c1228',
        'editorLineNumber.foreground': '#766b85',
        'editorGutter.background': '#160e20',
        'editor.selectionBackground': '#33234a',
        'editorCursor.foreground': '#a96fe0',
      },
    });

    monaco.editor.defineTheme('guardian-light', {
      base: 'vs',
      inherit: true,
      rules: [],
      colors: {
        'editor.background': '#ffffff',
        'editor.lineHighlightBackground': '#f6f3fa',
        'editorLineNumber.foreground': '#9a93a6',
        'editorGutter.background': '#ffffff',
        'editor.selectionBackground': '#f3ebf9',
        'editorCursor.foreground': '#8439c6',
      },
    });

    this.editor = monaco.editor.create(container, {
      value: initial,
      language: LANG_MAP[lang] || lang,
      theme: theme === 'dark' ? 'guardian-dark' : 'guardian-light',
      automaticLayout: true,
      minimap: { enabled: false },
      fontSize: 14,
      lineNumbers: 'on',
      scrollBeyondLastLine: false,
      wordWrap: 'on',
      tabSize: 4,
      insertSpaces: true,
      renderWhitespace: 'none',
      padding: { top: 12 },
      overviewRulerLanes: 0,
      hideCursorInOverviewRuler: true,
      overviewRulerBorder: false,
      scrollbar: { useShadows: false },
      hover: { enabled: false },
      quickSuggestions: false,
      suggestOnTriggerCharacters: false,
      parameterHints: { enabled: false },
      inlineSuggest: { enabled: false },
      codeLens: false,
    } as any);

    // intentional console.error override that only suppresses Monaco Editor's internal "Canceled" errors
    if (!CodeEditorComponent.monacoErrorSuppressed) {
      CodeEditorComponent.monacoErrorSuppressed = true;
      const orig = console.error;
      console.error = (...args: any[]) => {
        const first = args[0];
        if (first && typeof first === 'object' && 'message' in first && first.message === 'Canceled') return;
        orig.apply(console, args);
      };
    }

    this.editor.onDidChangeModelContent(() => {
      const value = this.editor.getValue();
      this.codeChange.emit(value);
      this.lineCount.set(this.editor.getModel()?.getLineCount() ?? 0);
    });

    if (initial) {
      this.codeChange.emit(initial);
      this.lineCount.set(this.editor.getModel()?.getLineCount() ?? 0);
    }
  }

  ngOnDestroy() {
    this.editor?.dispose();
  }
}
