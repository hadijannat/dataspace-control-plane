"""Data-plane HTTP request decoration for EDC consumer transfers.

Mirrors EDC's ``HttpRequestParamsProvider`` pattern: on the consumer side the
data-plane must receive the ``transferId`` and ``contractId`` so it can
validate entitlements before proxying the data request.

This module is intentionally free of I/O — callers obtain a
``TransferDecoration`` from the negotiation/transfer state and attach it to
outgoing HTTP headers themselves.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TransferDecoration:
    """Immutable decoration for EDC data-plane HTTP requests.

    Attach :meth:`as_headers` to outgoing requests so the EDC data-plane can
    authenticate and authorise the consumer data access.

    Header semantics:
    - ``Edc-Transfer-Id``: links the request to a running ``TransferProcess``.
    - ``Edc-Contract-Id``: allows the data-plane to verify the contract is
      still in a valid, non-expired state.
    """

    transfer_id: str
    contract_id: str

    def as_headers(self) -> dict[str, str]:
        """Return the decoration as an HTTP header dict ready for injection.

        Example::
            headers = decoration.as_headers()
            # {"Edc-Transfer-Id": "...", "Edc-Contract-Id": "..."}
        """
        return {
            "Edc-Transfer-Id": self.transfer_id,
            "Edc-Contract-Id": self.contract_id,
        }
