export function formatDate(iso: string): string {
  return new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(iso));
}

export function truncate(str: string, maxLen: number = 40): string {
  return str.length > maxLen ? `${str.slice(0, maxLen)}…` : str;
}

export function workflowIdToLabel(wid: string): string {
  // "company-onboarding-<uuid>" → "company-onboarding / <uuid-short>"
  const parts = wid.split('-');
  const uuid = parts.slice(-5).join('-');
  const prefix = parts.slice(0, -5).join('-');
  return prefix ? `${prefix} / ${uuid.slice(0, 8)}` : uuid.slice(0, 8);
}
