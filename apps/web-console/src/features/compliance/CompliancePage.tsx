import { PageLayout } from '../../shared/layout';
import { EmptyState } from '../../shared/ui';

export function CompliancePage() {
  return (
    <PageLayout title="Compliance" description="Regulatory pack status and evidence bundles.">
      <EmptyState title="Coming soon" description="This section is under construction." />
    </PageLayout>
  );
}
