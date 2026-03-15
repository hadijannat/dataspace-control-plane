import { PageLayout } from '../../shared/layout';
import { EmptyState } from '../../shared/ui';

export function ContractsPage() {
  return (
    <PageLayout title="Contracts" description="Contract negotiations, agreements, and evidence.">
      <EmptyState title="Coming soon" description="This section is under construction." />
    </PageLayout>
  );
}
