"""Workflow ID builders and activity idempotency key helpers."""

def workflow_id(*parts: str) -> str:
    """Build a canonical workflow ID from ordered parts, joined by ':'."""
    return ":".join(str(p) for p in parts if p)


def child_workflow_id(parent_id: str, *parts: str) -> str:
    """Build a child workflow ID scoped under a parent."""
    return f"{parent_id}:{':'.join(str(p) for p in parts if p)}"


def activity_key(workflow_id: str, activity_name: str, *disambiguators: str) -> str:
    """Build an idempotency key for a specific activity invocation."""
    parts = [workflow_id, activity_name, *disambiguators]
    return ":".join(str(p) for p in parts if p)
