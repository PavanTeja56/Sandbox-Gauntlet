import re
from app.security.audit import audit_logger


class CommandBlockedError(Exception):
    """Raised when a command violates safety policy and is blocked before VM execution."""
    def __init__(self, command: str, reason: str):
        self.command = command
        self.reason = reason
        super().__init__(f"Command blocked by safety hook: {reason} | Command: {command}")


class SafetyPolicy:
    """Pre-execution safety policy hooks."""

    PROHIBITED_PATTERNS = [
        (re.compile(r"\brm\s+-(?:rf|fr)\s+/(?:\s|$)", re.IGNORECASE), "Destructive root filesystem deletion prohibited"),
        (re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:", re.IGNORECASE), "Fork bomb attack pattern blocked"),
        (re.compile(r"\bmkfs(?:\.\w+)?\s+", re.IGNORECASE), "Raw filesystem destruction blocked"),
        (re.compile(r"\bdd\s+if=.*?of=/dev/[sh]d", re.IGNORECASE), "Direct block device write blocked"),
        (re.compile(r"\b(?:curl|wget|nc|bash -i)\b.*?(?:pastebin|attacker|evil|exfil)", re.IGNORECASE), "Unauthorized data exfiltration endpoint blocked"),
        (re.compile(r"\b(?:pip|npm)\s+install\s+.*?(?:malicious-|evil-|stealer-|pypi-malware)", re.IGNORECASE), "Suspicious package installation blocked"),
        (re.compile(r"cat\s+.*?(?:\.env|id_rsa|master_key)", re.IGNORECASE), "Unauthorized credential access blocked")
    ]

    @classmethod
    def evaluate_command(cls, sandbox_name: str, command: str) -> None:
        """Inspect command before execution. Logs allow/block decision and raises CommandBlockedError if unsafe."""
        for pattern, reason in cls.PROHIBITED_PATTERNS:
            if pattern.search(command):
                audit_logger.log_command(
                    sandbox_name=sandbox_name,
                    command=command,
                    decision="block",
                    execution_target="celesto_sandbox"
                )
                raise CommandBlockedError(command, reason)

        # Command passed safety check
        audit_logger.log_command(
            sandbox_name=sandbox_name,
            command=command,
            decision="allow",
            execution_target="celesto_sandbox"
        )
