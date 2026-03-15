from src.commands.apply import run_apply
from src.models.diff import ChangeSeverity, StateChange, StateDiff


class _CheckpointDouble:
    def __init__(self):
        self.store = {}

    def load(self, key):
        return self.store.get(key)

    def save(self, key, data):
        self.store[key] = data

    def delete(self, key):
        self.store.pop(key, None)


async def _noop_dispatch(change):
    return None


def test_run_apply_skips_checkpointed_change(monkeypatch, tmp_path):
    checkpoints = _CheckpointDouble()
    change = StateChange(
        resource_type="tenant_bootstrap",
        resource_id="tenant-a",
        operation="create",
        severity=ChangeSeverity.REVIEW,
        description="bootstrap tenant",
        details={"tenant_id": "tenant-a"},
    )
    checkpoints.save("tenant_bootstrap/tenant-a", change.details)

    monkeypatch.setattr("src.commands.apply.CheckpointManager", lambda _: checkpoints)
    monkeypatch.setattr("src.commands.apply._dispatch_change", _noop_dispatch)

    import asyncio

    asyncio.run(run_apply(StateDiff(changes=[change]), dry_run=False))

    assert checkpoints.load("tenant_bootstrap/tenant-a") == {"tenant_id": "tenant-a"}
