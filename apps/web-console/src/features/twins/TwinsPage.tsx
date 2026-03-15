import { PageLayout } from '../../shared/layout';
import { EmptyState } from '../../shared/ui';

export function TwinsPage() {
  return (
    <PageLayout title="Twins" description="Twin publication and AAS submodel status.">
      <EmptyState title="Coming soon" description="This section is under construction." />
    </PageLayout>
  );
}
