from app.services.procedure_catalog import ProcedureCatalog


def test_catalog_discovers_procedure_manifests():
    catalog = ProcedureCatalog.discover()

    definition = catalog.resolve("company-onboarding")
    assert definition.workflow_type == "CompanyOnboardingWorkflow"
    assert definition.task_queue == "onboarding"


def test_catalog_builds_workflow_input_and_search_attributes():
    catalog = ProcedureCatalog.discover()
    definition = catalog.resolve("company-onboarding")

    workflow_input = catalog.build_workflow_input(
        definition,
        tenant_id="tenant-a",
        legal_entity_id="lei-1",
        idempotency_key="idem-1",
        payload={
            "legal_entity_name": "ACME GmbH",
            "bpnl": "BPNL000000000001",
            "jurisdiction": "DE",
            "contact_email": "ops@example.com",
            "connector_url": "https://connector.example.com",
        },
    )

    workflow_id = catalog.build_workflow_id(definition, workflow_input)
    search_attributes = catalog.build_search_attributes(definition, workflow_input)

    assert workflow_id == "company-onboarding:tenant-a:lei-1"
    assert search_attributes["tenant_id"] == ["tenant-a"]
    assert search_attributes["legal_entity_id"] == ["lei-1"]
    assert search_attributes["procedure_type"] == ["company-onboarding"]
