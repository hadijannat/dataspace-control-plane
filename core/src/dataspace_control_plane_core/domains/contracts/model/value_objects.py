from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from dataspace_control_plane_core.canonical_models.contract import AssetRef, CounterpartyRef


@dataclass(frozen=True)
class OfferSnapshot:
    offer_id: str
    policy_id: str
    asset: AssetRef
    provider: CounterpartyRef
    valid_until: datetime | None = None


@dataclass(frozen=True)
class AgreementRecord:
    agreement_id: str
    policy_snapshot_id: str
    asset: AssetRef
    provider: CounterpartyRef
    consumer: CounterpartyRef
    concluded_at: datetime

    def is_valid_for_asset(self, asset_id: str) -> bool:
        return self.asset.asset_id == asset_id


@dataclass(frozen=True)
class TransferAuthorization:
    authorization_id: str
    agreement_id: str
    asset_id: str
    granted_at: datetime
    valid_until: datetime | None = None
    is_revoked: bool = False
