"""
Test-suite bootstrap for apps/control-api.

Sets CONTROL_API_DEBUG=true before any app module is imported so that the
stream_ticket_secret validator skips its production-only length/default checks.
This must run before any app module is imported, which conftest.py guarantees
because pytest processes it first.
"""
import os

os.environ.setdefault("CONTROL_API_DEBUG", "true")
os.environ.setdefault(
    "CONTROL_API_STREAM_TICKET_SECRET",
    "test-stream-ticket-secret-0123456789012345",
)
