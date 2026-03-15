"""Create and return a configured Temporal client."""
import structlog
from temporalio.client import Client, TLSConfig

from src.settings import settings

logger = structlog.get_logger(__name__)


async def create_temporal_client() -> Client:
    tls: TLSConfig | None = None
    if settings.temporal_tls:
        import pathlib
        tls = TLSConfig(
            client_cert=pathlib.Path(settings.temporal_tls_cert_path).read_bytes() if settings.temporal_tls_cert_path else None,
            client_private_key=pathlib.Path(settings.temporal_tls_key_path).read_bytes() if settings.temporal_tls_key_path else None,
        )
    client = await Client.connect(
        settings.temporal_host,
        namespace=settings.temporal_namespace,
        tls=tls,
    )
    logger.info("temporal.client_connected", host=settings.temporal_host, namespace=settings.temporal_namespace)
    return client
