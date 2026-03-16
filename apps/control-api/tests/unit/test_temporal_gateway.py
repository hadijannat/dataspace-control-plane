import pytest

from app.application.commands.procedures import StartProcedureCommand
from app.services.procedure_catalog import ProcedureCatalog
from app.services.temporal_gateway import TemporalGateway


class FakeWorkflowHandle:
    def __init__(self, workflow_id: str):
        self.id = workflow_id
        self.first_execution_run_id = f"run:{workflow_id}"


class FakeTemporalClient:
    def __init__(self):
        self.calls = []

    async def start_workflow(self, workflow, arg=object(), **kwargs):
        self.calls.append({
            "workflow": workflow,
            "arg": arg,
            **kwargs,
        })
        return FakeWorkflowHandle(kwargs["id"])


@pytest.mark.asyncio
async def test_gateway_uses_manifest_backed_dispatch():
    client = FakeTemporalClient()
    gateway = TemporalGateway(client)
    catalog = ProcedureCatalog.discover()

    handle = await gateway.start_procedure(
        StartProcedureCommand(
            procedure_type="company-onboarding",
            tenant_id="tenant-a",
            legal_entity_id="lei-1",
            payload={
                "legal_entity_name": "ACME GmbH",
                "bpnl": "BPNL000000000001",
                "jurisdiction": "DE",
                "contact_email": "ops@example.com",
                "connector_url": "https://connector.example.com",
            },
            idempotency_key="idem-1",
            actor_subject="operator-1",
        ),
        catalog,
    )

    assert handle.workflow_id == "company-onboarding:tenant-a:lei-1"
    assert handle.run_id == "run:company-onboarding:tenant-a:lei-1"
    assert client.calls[0]["workflow"] == "CompanyOnboardingWorkflow"
    assert client.calls[0]["task_queue"] == "onboarding"
    assert client.calls[0]["search_attributes"]["procedure_type"] == ["company-onboarding"]
    assert client.calls[0]["search_attributes"]["status"] == ["running"]
