type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info';

const STATUS_VARIANT_MAP: Record<string, BadgeVariant> = {
  RUNNING: 'info',
  COMPLETED: 'success',
  FAILED: 'error',
  CANCELLED: 'warning',
  TIMED_OUT: 'error',
  ACTIVE: 'success',
  INACTIVE: 'default',
};

interface BadgeProps {
  label: string;
  variant?: BadgeVariant;
  status?: string; // auto-maps to variant
}

export function Badge({ label, variant, status }: BadgeProps) {
  const v = variant ?? (status ? (STATUS_VARIANT_MAP[status] ?? 'default') : 'default');
  const colors = {
    default: 'bg-gray-100 text-gray-700',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    error: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
  };
  return <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[v]}`}>{label}</span>;
}
