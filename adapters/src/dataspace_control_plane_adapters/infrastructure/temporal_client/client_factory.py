"""Temporal client factory.

Builds a connected temporalio.client.Client from TemporalClientSettings.
Handles TLS configuration, API key injection, and connection validation.

Usage:
    from dataspace_control_plane_adapters.infrastructure.temporal_client.client_factory import (
        create_temporal_client,
    )
    client = await create_temporal_client(cfg)
"""
from __future__ import annotations

import logging
import ssl
from typing import TYPE_CHECKING

from .config import TemporalClientSettings
from .errors import TemporalConnectionError

if TYPE_CHECKING:
    import temporalio.client

logger = logging.getLogger(__name__)


async def create_temporal_client(
    cfg: TemporalClientSettings,
) -> "temporalio.client.Client":
    """Build and return a connected Temporal client.

    Supports three connection modes, selected by which cfg fields are set:
    1. Plain gRPC (local/dev): neither api_key nor tls_cert_path are set.
    2. mTLS: tls_cert_path and tls_key_path are set (self-hosted or Temporal Cloud mTLS).
    3. API key (Temporal Cloud): api_key is set.

    Args:
        cfg: TemporalClientSettings populated from environment or defaults.

    Returns:
        Connected ``temporalio.client.Client`` instance.

    Raises:
        TemporalConnectionError: The client cannot connect to the Temporal server.
    """
    # Heavy SDK import deferred to avoid mandatory dependency at module load time.
    import temporalio.client

    target = f"{cfg.host}:{cfg.port}"

    try:
        tls_config = _build_tls_config(cfg)

        # Build runtime with connection options
        connect_kwargs: dict[str, object] = {
            "target_host": target,
            "namespace": cfg.namespace,
            "tls": tls_config,
        }

        # Inject API key as RPC metadata if provided (Temporal Cloud)
        if cfg.api_key is not None:
            connect_kwargs["api_key"] = cfg.api_key.get_secret_value()

        client = await temporalio.client.Client.connect(**connect_kwargs)  # type: ignore[arg-type]
        logger.info(
            "Connected to Temporal server at %s namespace=%s", target, cfg.namespace
        )
        return client

    except Exception as exc:
        raise TemporalConnectionError(
            f"Failed to connect to Temporal server at {target} namespace={cfg.namespace!r}: {exc}"
        ) from exc


def _build_tls_config(cfg: TemporalClientSettings) -> "bool | temporalio.client.TLSConfig":
    """Build Temporal TLS configuration from settings.

    Returns:
        False   — no TLS (plain gRPC)
        True    — TLS with default system CA (no client cert)
        TLSConfig — full mTLS with explicit cert paths
    """
    import temporalio.client

    if cfg.tls_cert_path is None and cfg.tls_key_path is None and cfg.tls_ca_path is None:
        # No TLS configured; use plain gRPC for local dev
        return False

    client_cert: bytes | None = None
    client_private_key: bytes | None = None
    server_root_ca_cert: bytes | None = None

    if cfg.tls_cert_path is not None and cfg.tls_key_path is not None:
        with open(cfg.tls_cert_path, "rb") as f:
            client_cert = f.read()
        with open(cfg.tls_key_path, "rb") as f:
            client_private_key = f.read()

    if cfg.tls_ca_path is not None:
        with open(cfg.tls_ca_path, "rb") as f:
            server_root_ca_cert = f.read()

    return temporalio.client.TLSConfig(
        client_cert=client_cert,
        client_private_key=client_private_key,
        server_root_ca_cert=server_root_ca_cert,
        domain=cfg.tls_server_name,
    )
