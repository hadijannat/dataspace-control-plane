import { createBrowserRouter } from 'react-router';
import { AppShell } from './app-shell';
import { RouteErrorBoundary } from './route-error-boundary';
import { getRuntimeConfig, type RuntimeConfig } from './runtime-config';
import { RequireAuth } from '../auth/require-auth';

// Route-level lazy imports — each feature loads only when the route is visited
const Dashboard = () => import('../routes/dashboard').then((m) => ({ Component: m.default }));
const Tenants = () => import('../routes/tenants').then((m) => ({ Component: m.default }));
const Procedures = () => import('../routes/procedures').then((m) => ({ Component: m.default }));
const Connectors = () => import('../routes/connectors').then((m) => ({ Component: m.default }));
const Twins = () => import('../routes/twins').then((m) => ({ Component: m.default }));
const Policies = () => import('../routes/policies').then((m) => ({ Component: m.default }));
const Contracts = () => import('../routes/contracts').then((m) => ({ Component: m.default }));
const Compliance = () => import('../routes/compliance').then((m) => ({ Component: m.default }));
const Metering = () => import('../routes/metering').then((m) => ({ Component: m.default }));

export interface RootLoaderData {
  runtimeConfig: RuntimeConfig;
}

async function rootLoader(): Promise<RootLoaderData> {
  return { runtimeConfig: getRuntimeConfig() };
}

export const router = createBrowserRouter([
  {
    id: 'root',
    path: '/',
    loader: rootLoader,
    errorElement: <RouteErrorBoundary />,
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      { index: true, lazy: Dashboard },
      { path: 'dashboard', lazy: Dashboard },
      { path: 'tenants', lazy: Tenants },
      { path: 'procedures', lazy: Procedures },
      { path: 'connectors', lazy: Connectors },
      { path: 'twins', lazy: Twins },
      { path: 'policies', lazy: Policies },
      { path: 'contracts', lazy: Contracts },
      { path: 'compliance', lazy: Compliance },
      { path: 'metering', lazy: Metering },
    ],
  },
]);
