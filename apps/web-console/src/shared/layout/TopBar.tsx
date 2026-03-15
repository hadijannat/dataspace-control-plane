import { useAuth } from '../../auth/auth-provider';

export function TopBar() {
  const { session, logout } = useAuth();
  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center justify-between px-6">
      <div className="text-sm text-gray-500">Dataspace Control Plane</div>
      <div className="flex items-center gap-4">
        {session.email && <span className="text-sm text-gray-700">{session.email}</span>}
        <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-900">Sign out</button>
      </div>
    </header>
  );
}
