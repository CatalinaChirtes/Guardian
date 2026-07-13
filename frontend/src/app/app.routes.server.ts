import { RenderMode, ServerRoute } from '@angular/ssr';

// Original server routes
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

// Study complete placeholder
// export const serverRoutes: ServerRoute[] = [
//   {
//     path: '**',
//     renderMode: RenderMode.Prerender,
//   },
// ];
