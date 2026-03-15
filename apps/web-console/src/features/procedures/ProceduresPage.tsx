import { useQuery } from '@tanstack/react-query';
import type { ColumnDef } from '@tanstack/react-table';
import { PageLayout } from '../../shared/layout';
import { DataTable } from '../../shared/tables';
import { Badge } from '../../shared/ui';
import { proceduresApi, type ProcedureStatus } from '../../generated/control-api-sdk';
import { workflowIdToLabel } from '../../shared/utils';
import { useActiveTenantId } from '../../auth/auth-provider';

const COLUMNS: ColumnDef<ProcedureStatus, unknown>[] = [
  { accessorKey: 'procedure_type', header: 'Type' },
  { accessorKey: 'status', header: 'Status', cell: ({ getValue }) => <Badge label={getValue() as string} status={getValue() as string} /> },
  { accessorKey: 'workflow_id', header: 'Workflow ID', cell: ({ getValue }) => <code className="text-xs">{workflowIdToLabel(getValue() as string)}</code> },
];

export function ProceduresPage() {
  const tenantId = useActiveTenantId();
  const { data, isLoading } = useQuery({
    queryKey: ['procedures', tenantId],
    queryFn: () => proceduresApi.list(tenantId ?? ''),
    enabled: tenantId !== null,
  });

  return (
    <PageLayout title="Procedures" description="Durable business procedures and their current status.">
      <DataTable
        data={data?.items ?? []}
        columns={COLUMNS}
        loading={isLoading}
        emptyMessage="No procedures found"
      />
    </PageLayout>
  );
}
