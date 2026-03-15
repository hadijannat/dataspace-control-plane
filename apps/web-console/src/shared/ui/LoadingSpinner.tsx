export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const s = { sm: 'h-4 w-4', md: 'h-8 w-8', lg: 'h-12 w-12' }[size];
  return <div className={`${s} animate-spin rounded-full border-2 border-gray-300 border-t-blue-600`} />;
}

export function PageLoader() {
  return <div className="flex items-center justify-center min-h-[400px]"><LoadingSpinner size="lg" /></div>;
}
