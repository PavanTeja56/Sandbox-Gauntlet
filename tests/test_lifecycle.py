import pytest
from app.celesto.adapter import CelestoAdapter, SandboxState


def test_sandbox_name_validation():
    # Valid name
    adapter = CelestoAdapter(sandbox_name="sbx-testlifecycle01")
    assert adapter.sandbox_name == "sbx-testlifecycle01"
    assert adapter.state == SandboxState.CREATED

    # Invalid names
    with pytest.raises(ValueError):
        CelestoAdapter(sandbox_name="invalid-prefix-12345678")

    with pytest.raises(ValueError):
        CelestoAdapter(sandbox_name="sbx-short")

    with pytest.raises(ValueError):
        CelestoAdapter(sandbox_name="sbx-UPPERCASE123")


def test_state_machine_valid_transitions():
    adapter = CelestoAdapter(sandbox_name="sbx-trans00000001")
    assert adapter.state == SandboxState.CREATED

    adapter._transition(SandboxState.READY)
    assert adapter.state == SandboxState.READY

    adapter._transition(SandboxState.RUNNING)
    assert adapter.state == SandboxState.RUNNING

    adapter._transition(SandboxState.SUCCEEDED)
    assert adapter.state == SandboxState.SUCCEEDED

    adapter._transition(SandboxState.DELETED)
    assert adapter.state == SandboxState.DELETED


def test_state_machine_invalid_transitions():
    adapter = CelestoAdapter(sandbox_name="sbx-invalid00001")
    # Cannot jump directly from created to succeeded
    with pytest.raises(ValueError):
        adapter._transition(SandboxState.SUCCEEDED)

    # Cannot transition out of deleted
    adapter._transition(SandboxState.DELETED)
    with pytest.raises(ValueError):
        adapter._transition(SandboxState.RUNNING)


def test_cleanup_handler():
    adapter = CelestoAdapter(sandbox_name="sbx-cleanup00001")
    adapter._transition(SandboxState.READY)
    cleaned = adapter.cleanup()
    assert cleaned is True
    assert adapter.state == SandboxState.DELETED
