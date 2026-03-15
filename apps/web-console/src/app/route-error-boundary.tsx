import { isRouteErrorResponse, useRouteError } from 'react-router';

export function RouteErrorBoundary() {
  const error = useRouteError();
  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : error instanceof Error
      ? error.message
      : 'Unknown route error';

  return (
    <div className="min-h-screen bg-gray-50 px-6 py-16">
      <div className="mx-auto max-w-2xl rounded-xl border border-red-200 bg-white p-8 shadow-sm">
        <p className="text-sm font-semibold uppercase tracking-wide text-red-600">Route Error</p>
        <h1 className="mt-3 text-2xl font-semibold text-gray-900">The operator console could not load this route.</h1>
        <p className="mt-3 text-sm text-gray-600">{message}</p>
      </div>
    </div>
  );
}

