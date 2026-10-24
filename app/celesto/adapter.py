import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.config import settings
from app.database import SessionLocal
from app.models import RunRecord
from app.security.hooks import SafetyPolicy, CommandBlockedError
from app.security.audit import audit_logger

# Import Celesto SDK if available
try:
    sys.path.insert(0, str(Path("celesto_sdk").resolve()))
    from celesto import Computer
    from _celesto_cloud_api.client import AuthenticatedClient
    from _celesto_cloud_api.api.computers import (
        get_computer_v1_computers_computer_id_get as get_computer,
        delete_computer_v1_computers_computer_id_delete as delete_computer,
    )
    CELESTO_SDK_AVAILABLE = True
except Exception:
    CELESTO_SDK_AVAILABLE = False


class SandboxState:
    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DELETED = "deleted"

    VALID_TRANSITIONS = {
        CREATED: {READY, FAILED, DELETED},
        READY: {RUNNING, FAILED, DELETED},
        RUNNING: {SUCCEEDED, FAILED, DELETED},
        SUCCEEDED: {DELETED},
        FAILED: {DELETED},
        DELETED: set(),
    }


class CelestoAdapter:
    """Production-minded adapter for Celesto microVM execution."""

    def __init__(self, sandbox_name: str, problem_id: str = "benign_task", run_id: str | None = None):
        if not sandbox_name.startswith("sbx-"):
            raise ValueError("sandbox_name must start with 'sbx-'")
        suffix = sandbox_name[4:]
        if len(suffix) < 8 or not re.match(r"^[a-z0-9]+$", suffix):
            raise ValueError("sandbox_name suffix must have at least 8 lowercase alphanumeric characters")

        self.sandbox_name = sandbox_name
        self.problem_id = problem_id
        self.run_id = run_id or f"run-{uuid.uuid4().hex[:12]}"
        self.state = SandboxState.CREATED
        self.computer_id: str | None = None
        self.computer = None
        self.boot_to_ready_s: float = 0.0
        self.wall_clock_s: float = 0.0
        self.cost_usd: float = 0.0
        self.created_at = datetime.now(timezone.utc)
        self.execution_target = "celesto_sandbox"
        self._record_run()

    def _transition(self, target_state: str):
        allowed = SandboxState.VALID_TRANSITIONS.get(self.state, set())
        if target_state not in allowed and target_state != self.state:
            raise ValueError(f"Invalid lifecycle transition from {self.state} to {target_state}")
        self.state = target_state
        self._update_run()

    def _record_run(self):
        """Persist initial run state to Run Ledger."""
        db = SessionLocal()
        try:
            rec = db.query(RunRecord).filter(RunRecord.run_id == self.run_id).first()
            if not rec:
                rec = RunRecord(
                    run_id=self.run_id,
                    sandbox_name=self.sandbox_name,
                    problem_id=self.problem_id,
                    state=self.state,
                    execution_target=self.execution_target,
                )
                db.add(rec)
            else:
                rec.state = self.state
            db.commit()
        finally:
            db.close()

    def _update_run(self):
        """Update existing run state in Run Ledger."""
        db = SessionLocal()
        try:
            rec = db.query(RunRecord).filter(RunRecord.run_id == self.run_id).first()
            if rec:
                rec.state = self.state
                db.commit()
        finally:
            db.close()

    def start_sandbox(self) -> None:
        """Create and boot a fresh Celesto sandbox."""
        start_t = time.perf_counter()
        self._transition(SandboxState.CREATED)

        if not CELESTO_SDK_AVAILABLE or not settings.CELESTO_API_KEY:
            self._transition(SandboxState.FAILED)
            raise RuntimeError("Celesto SDK or CELESTO_API_KEY is not configured.")

        try:
            # Connect to Celesto Cloud
            self.computer = Computer(provider="cloud")
            self.computer._ensure_started()
            self.computer_id = getattr(self.computer, "id", None) or getattr(self.computer._provider, "vm_id", None)
            ready_t = time.perf_counter()
            self.boot_to_ready_s = round(ready_t - start_t, 3)
            self._transition(SandboxState.READY)
        except Exception as e:
            self._transition(SandboxState.FAILED)
            # Record honest error without falling back to host execution
            raise RuntimeError(f"Celesto sandbox creation failed: {e}")

    def execute_command(self, command: str) -> dict[str, Any]:
        """Execute a command inside the Celesto sandbox with pre-execution safety hooks."""
        # Enforce pre-execution hook inspection
        SafetyPolicy.evaluate_command(sandbox_name=self.sandbox_name, command=command)

        if self.state not in (SandboxState.READY, SandboxState.RUNNING):
            raise RuntimeError(f"Cannot execute command in state '{self.state}'. Must be ready or running.")

        self._transition(SandboxState.RUNNING)

        if not self.computer:
            raise RuntimeError("Execution failed: No active Celesto microVM connection.")

        exec_start = time.perf_counter()
        res = self.computer.run(command)
        duration = round(time.perf_counter() - exec_start, 3)

        return {
            "command": command,
            "exit_code": getattr(res, "exit_code", 0),
            "stdout": getattr(res, "stdout", ""),
            "stderr": getattr(res, "stderr", ""),
            "duration_s": duration
        }

    def cleanup(self) -> bool:
        """Clean up and delete the Celesto sandbox, verifying final state."""
        success = False
        try:
            if self.computer:
                try:
                    self.computer.delete()
                    success = True
                except Exception:
                    pass
            else:
                success = True
        finally:
            self._transition(SandboxState.DELETED)
        return success
