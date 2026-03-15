import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { PageLayout } from '../../shared/layout';
import { DataTable } from '../../shared/tables';
import { Badge } from '../../shared/ui';
import { tenantsApi, type Tenant } from '../../generated/control-api-sdk';

const COLUMNS: ColumnDef<Tenant, unknown>[] = [
  { accessorKey: 'tenant_id', header: 'Tenant ID' },
  { accessorKey: 'display_name', header: 'Name' },
  { accessorKey: 'legal_entity_id', header: 'Legal Entity ID' },
  { accessorKey: 'status', header: 'Status', cell: ({ getValue }) => <Badge label={getValue() as string} status={getValue() as string} /> },
];

export function TenantsPage() {
  const { data, isLoading } = useQuery({
    queryKey: ['tenants'],
    queryFn: () => tenantsApi.list({ limit: 50, offset: 0 }),
  });

  return (
    <PageLayout title="Tenants" description="Registered tenants in this dataspace instance.">
      <DataTable data={data?.items ?? []} columns={COLUMNS} loading={isLoading} emptyMessage="No tenants registered" />
    </PageLayout>
  );
}
