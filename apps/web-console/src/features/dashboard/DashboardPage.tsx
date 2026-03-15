import { PageLayout } from '../../shared/layout';
import { Card } from '../../shared/ui';

export function DashboardPage() {
  return (
    <PageLayout title="Dashboard" description="System health, active procedures, and recent events.">
      <Card title="Welcome to Dataspace Control Plane" description="Monitor and manage your dataspace from this operator console.">
        <p className="text-sm text-gray-600">
          Use the navigation sidebar to access tenants, procedures, connectors, digital twins, contracts, policies, compliance packs, and metering data.
        </p>
      </Card>
    </PageLayout>
  );
}
