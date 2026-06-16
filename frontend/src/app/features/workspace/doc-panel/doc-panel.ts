import { Component, DestroyRef, inject, signal, output, OnInit } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { ApiService } from '../../../core/services/api.service';
import { CurriculumDocument } from '../../../core/models/interfaces';
import { NgClass } from '@angular/common';
import { IconComponent } from '../../../shared/components/icon/icon';

@Component({
  selector: 'app-doc-panel',
  imports: [NgClass, IconComponent],
  templateUrl: './doc-panel.html',
  styleUrl: './doc-panel.css',
})
export class DocPanelComponent implements OnInit {
  docs = signal<CurriculumDocument[]>([]);
  docsChanged = output<number>();
  private destroyRef = inject(DestroyRef);
  uploading = signal(false);
  uploadError = signal('');
  uploadSuccess = signal('');
  maxDocs = 10;

  private api = inject(ApiService);

  ngOnInit() {
    this.loadDocs();
  }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;
    input.value = '';

    const allowedTypes = ['application/pdf', 'text/plain'];
    if (!allowedTypes.includes(file.type)) {
      this.uploadError.set('Only PDF and TXT files are allowed');
      return;
    }

    const maxSize = 50 * 1024 * 1024;
    if (file.size > maxSize) {
      this.uploadError.set('File too large (max 50MB)');
      return;
    }

    this.uploading.set(true);
    this.uploadError.set('');
    this.uploadSuccess.set('');
    this.api.uploadCurriculum(file).subscribe({
      next: (doc) => {
        this.uploading.set(false);
        this.uploadSuccess.set(`"${doc.filename}" uploaded (${doc.chunk_count} chunks)`);
        this.loadDocs();
        setTimeout(() => this.uploadSuccess.set(''), 4000);
      },
      error: (err) => {
        this.uploading.set(false);
        this.uploadError.set(err.error?.detail ?? 'Upload failed');
      },
    });
  }

  deletingId = signal<string | null>(null);

  deleteDoc(docId: string) {
    this.deletingId.set(docId);
    this.api.deleteCurriculum(docId).subscribe({
      next: () => {
        this.deletingId.set(null);
        this.loadDocs();
      },
      error: (err) => {
        this.deletingId.set(null);
        this.uploadError.set(err.error?.detail ?? 'Delete failed');
      },
    });
  }

  private loadDocs() {
    this.api.listCurriculum().pipe(takeUntilDestroyed(this.destroyRef)).subscribe({
      next: (docs) => {
        this.docs.set(docs);
        this.docsChanged.emit(docs.length);
      },
      error: () => {},
    });
  }
}
