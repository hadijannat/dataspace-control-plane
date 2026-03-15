import { Outlet } from 'react-router';
import { Sidebar } from '../shared/layout/Sidebar';
import { TopBar } from '../shared/layout/TopBar';

export function AppShell() {
  return (
    <div className="flex h-screen bg-gray-50">
      <Sidebar />
      <div className="flex-1 flex flex-col ml-60 min-h-screen">
        <TopBar />
        <main className="flex-1 overflow-y-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
