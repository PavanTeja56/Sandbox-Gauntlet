import json
import os
from datetime import datetime, timezone
from pathlib import Path

COMMAND_LOG_PATH = Path("logs/commands.jsonl")


class AuditLogger:
    def __init__(self, log_path: Path = COMMAND_LOG_PATH):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_command(
        self,
        sandbox_name: str,
        command: str,
        decision: str,
        execution_target: str = "celesto_sandbox",
        timestamp: str | None = None
    ) -> dict:
        """Log a command attempt to logs/commands.jsonl.
        
        Fields:
        - ts: ISO-8601 string
        - sandbox_name: matches sbx- plus 8 or more lowercase letters or digits
        - command: non-empty string
        - decision: allow or block
        - execution_target: celesto_sandbox
        """
        if decision not in ("allow", "block"):
            raise ValueError("decision must be either 'allow' or 'block'")
        if execution_target != "celesto_sandbox":
            raise ValueError("execution_target must be exactly 'celesto_sandbox'")

        entry = {
            "ts": timestamp or datetime.now(timezone.utc).isoformat(),
            "sandbox_name": sandbox_name,
            "command": command,
            "decision": decision,
            "execution_target": execution_target,
        }

        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        return entry


audit_logger = AuditLogger()
