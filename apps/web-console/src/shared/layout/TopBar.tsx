import { useRouteLoaderData } from 'react-router';

import { useAuth } from '../../auth/auth-provider';
import type { RootLoaderData } from '../../app/router';

export function TopBar() {
  const { session, logout } = useAuth();
  const rootData = useRouteLoaderData('root') as RootLoaderData | undefined;
  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div className="flex items-center gap-3">
        <div className="text-sm text-gray-500">Dataspace Control Plane</div>
        {rootData?.runtimeConfig.tenantBanner ? (
          <span className="rounded-full bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700">
            {rootData.runtimeConfig.tenantBanner}
          </span>
        ) : null}
      </div>
      <div className="flex items-center gap-4">
        {session.email && <span className="text-sm text-gray-700">{session.email}</span>}
        <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-900">Sign out</button>
      </div>
    </header>
  );
}
