"""Low-level async S3 client wrapper.

Wraps aiobotocore to provide a consistent async context-manager client
for S3-compatible object storage. Credentials and endpoint are fully
encapsulated — callers never handle raw boto3/aiobotocore sessions.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

from .config import ObjectStorageSettings
from .errors import ObjectStorageError

logger = logging.getLogger(__name__)


@asynccontextmanager
async def s3_client(settings: ObjectStorageSettings):  # type: ignore[return]
    """Async context manager that yields a configured aiobotocore S3 client.

    Usage::

        async with s3_client(settings) as s3:
            resp = await s3.head_object(Bucket="my-bucket", Key="my-key")

    Raises:
        ObjectStorageError: If aiobotocore is not installed.
    """
    try:
        import aiobotocore.session as _ab_session  # type: ignore[import]
    except ImportError as exc:
        raise ObjectStorageError(
            "aiobotocore is not installed. Install it with: pip install aiobotocore"
        ) from exc

    session = _ab_session.get_session()
    client_kwargs: dict[str, Any] = {
        "service_name": "s3",
        "region_name": settings.region,
        "aws_access_key_id": settings.access_key_id,
        "aws_secret_access_key": settings.secret_access_key.get_secret_value(),
    }
    if settings.session_token:
        client_kwargs["aws_session_token"] = settings.session_token.get_secret_value()
    if settings.endpoint_url:
        client_kwargs["endpoint_url"] = settings.endpoint_url
    if settings.use_path_style:
        client_kwargs["config"] = _build_path_style_config()

    async with session.create_client(**client_kwargs) as client:
        yield client


def _build_path_style_config() -> Any:
    try:
        from botocore.config import Config  # type: ignore[import]

        return Config(s3={"addressing_style": "path"})
    except ImportError:
        return None
