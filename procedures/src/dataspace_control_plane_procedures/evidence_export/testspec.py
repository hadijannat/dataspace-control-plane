from dataclasses import dataclass


@dataclass
class EvidenceExportScenarios:
    happy_path_quarterly: str = "happy_path_quarterly"
    dry_run_mode: str = "dry_run_mode"
    kms_signing_retry: str = "kms_signing_retry"
    storage_failure: str = "storage_failure"
    scheduled_monthly_bundle: str = "scheduled_monthly_bundle"
    nightly_ledger_bundle: str = "nightly_ledger_bundle"


SCENARIOS = EvidenceExportScenarios()
