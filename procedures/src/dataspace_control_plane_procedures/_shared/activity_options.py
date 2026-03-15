from datetime import timedelta
from temporalio.common import RetryPolicy

# Retry policies
SHORT_RETRY = RetryPolicy(
    maximum_attempts=3,
    initial_interval=timedelta(seconds=2),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(seconds=30),
)
STANDARD_RETRY = RetryPolicy(
    maximum_attempts=10,
    initial_interval=timedelta(seconds=5),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=5),
)
UNLIMITED_RETRY = RetryPolicy(
    maximum_attempts=0,  # unlimited — use only for idempotent activities
    initial_interval=timedelta(seconds=10),
    backoff_coefficient=2.0,
    maximum_interval=timedelta(minutes=10),
)

# Activity option dicts (pass as **kwargs to workflow.execute_activity)
RPC_OPTIONS: dict = dict(
    start_to_close_timeout=timedelta(seconds=30),
    retry_policy=SHORT_RETRY,
)
EXTERNAL_CALL_OPTIONS: dict = dict(
    start_to_close_timeout=timedelta(minutes=2),
    retry_policy=STANDARD_RETRY,
)
PROVISIONING_OPTIONS: dict = dict(
    start_to_close_timeout=timedelta(minutes=10),
    heartbeat_timeout=timedelta(seconds=30),
    retry_policy=STANDARD_RETRY,
)
LONG_POLL_OPTIONS: dict = dict(
    schedule_to_close_timeout=timedelta(hours=24),
    heartbeat_timeout=timedelta(minutes=5),
    retry_policy=UNLIMITED_RETRY,
)
EXPORT_OPTIONS: dict = dict(
    start_to_close_timeout=timedelta(minutes=30),
    heartbeat_timeout=timedelta(minutes=2),
    retry_policy=STANDARD_RETRY,
)
