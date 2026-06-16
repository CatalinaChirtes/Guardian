import { RenderMode, ServerRoute } from '@angular/ssr';

export const serverRoutes: ServerRoute[] = [
  {
    path: 'workspace/:id',
    renderMode: RenderMode.Client,
  },
  {
    path: 'workspace',
    renderMode: RenderMode.Client,
  },
  {
    path: 'practice',
    renderMode: RenderMode.Client,
  },
  {
    path: '**',
    renderMode: RenderMode.Prerender,
  },
];
