import { ErrorHandler, Injectable } from '@angular/core';
import { environment } from '../../../environments/environment';

@Injectable()
export class GlobalErrorHandler implements ErrorHandler {
  handleError(error: unknown): void {
    const message = error instanceof Error ? error.message : String(error);

    if (message.includes('Canceled') || message.includes('ExpressionChangedAfterItHasBeenCheckedError')) {
      return;
    }

    if (!environment.production) {
      console.error('[Guardian] Unhandled error:', error);
    }
  }
}
