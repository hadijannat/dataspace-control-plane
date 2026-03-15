import { PageLayout } from '../../shared/layout';
import { EmptyState } from '../../shared/ui';

export function PoliciesPage() {
  return (
    <PageLayout title="Policies" description="ODRL policy authoring and profile management.">
      <EmptyState title="Coming soon" description="This section is under construction." />
    </PageLayout>
  );
}
