import { NavLink } from 'react-router';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Dashboard', icon: '🏠' },
  { to: '/tenants', label: 'Tenants', icon: '🏢' },
  { to: '/procedures', label: 'Procedures', icon: '⚙️' },
  { to: '/connectors', label: 'Connectors', icon: '🔌' },
  { to: '/twins', label: 'Twins', icon: '🪞' },
  { to: '/contracts', label: 'Contracts', icon: '📄' },
  { to: '/policies', label: 'Policies', icon: '📋' },
  { to: '/compliance', label: 'Compliance', icon: '✅' },
  { to: '/metering', label: 'Metering', icon: '📊' },
  { to: '/settings', label: 'Settings', icon: '⚙️' },
];

export function Sidebar() {
  return (
    <nav className="w-60 bg-gray-900 text-gray-100 flex flex-col h-screen fixed left-0 top-0">
      <div className="px-6 py-5 border-b border-gray-700">
        <span className="text-lg font-bold">Dataspace CP</span>
      </div>
      <ul className="flex-1 overflow-y-auto py-4 space-y-1 px-3">
        {NAV_ITEMS.map(({ to, label, icon }) => (
          <li key={to}>
            <NavLink
              to={to}
              className={({ isActive }) =>
                `flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  isActive ? 'bg-blue-600 text-white' : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`
              }
            >
              <span>{icon}</span>
              <span>{label}</span>
            </NavLink>
          </li>
        ))}
      </ul>
    </nav>
  );
}
