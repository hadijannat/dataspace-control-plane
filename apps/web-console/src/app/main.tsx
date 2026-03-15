/**
 * Application entry point.
 * 1. Fetch runtime config (before React mounts — prevents flicker from config load).
 * 2. Mount React with Providers + RouterProvider.
 */
import { StrictMode } from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from 'react-router';
import { loadRuntimeConfig } from './runtime-config';
import { Providers } from './providers';
import { router } from './router';

async function bootstrap() {
  await loadRuntimeConfig();
  const root = document.getElementById('root');
  if (!root) throw new Error('#root element not found');
  ReactDOM.createRoot(root).render(
    <StrictMode>
      <Providers>
        <RouterProvider router={router} />
      </Providers>
    </StrictMode>,
  );
}

bootstrap().catch(console.error);
