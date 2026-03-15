import { PageLayout } from '../../shared/layout';
import { EmptyState } from '../../shared/ui';

export function SettingsPage() {
  return (
    <PageLayout title="Settings" description="Operator environment and configuration.">
      <EmptyState title="Coming soon" description="This section is under construction." />
    </PageLayout>
  );
}
