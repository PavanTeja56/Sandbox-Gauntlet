import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class SafetyPassport:
    """The signature output of Sandbox Gauntlet: An evidence-backed passport

    evaluating Utility, Security, Reliability, and Recovery dimensions.
    """

    def __init__(self, run_id: str, execution_env: str = "celesto_sandbox"):
        self.run_id = run_id
        self.execution_env = execution_env
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.dimensions: dict[str, Any] = {}
        self.limitations: list[str] = []
        self.blocked_checks: list[str] = []
        self.evidence_references: list[str] = []

    def set_utility(self, passed: bool, score: float, task_name: str, evidence: str):
        self.dimensions["utility"] = {
            "task_name": task_name,
            "status": "PASSED" if passed else "FAILED",
            "score": score,
            "evidence": evidence,
            "description": "Deterministic validation of agent computational artifacts against independently calculated baseline."
        }
        self.evidence_references.append(evidence)

    def set_security(self, contained: bool, scenarios_evaluated: list[dict[str, Any]], evidence: str):
        self.dimensions["security"] = {
            "contained": contained,
            "scenarios_evaluated": scenarios_evaluated,
            "evidence": evidence,
            "description": "Pre-execution hooks and microVM boundary containment stopping adversarial exfiltration, destructive commands, and malicious packages."
        }
        self.evidence_references.append(evidence)

    def set_reliability(self, metrics: dict[str, Any], evidence: str):
        self.dimensions["reliability"] = {
            **metrics,
            "evidence": evidence,
            "description": "Repeatable evaluation across independent fresh sandboxes calculating success rate, median/p90 wall-clock time, boot-to-ready time, and cost."
        }
        self.evidence_references.append(evidence)

    def set_recovery(self, policy: str, step_failed: int, total_steps: int, recovered: bool, evidence: str):
        self.dimensions["recovery"] = {
            "policy": policy,
            "step_failed": step_failed,
            "total_steps": total_steps,
            "recovered": recovered,
            "evidence": evidence,
            "description": "Lifecycle recovery policy applied to step-7-of-10 simulated crash with timestamped event audit trail."
        }
        self.evidence_references.append(evidence)

    def add_limitation(self, limitation: str):
        self.limitations.append(limitation)

    def add_blocked_check(self, check_name: str, reason: str):
        self.blocked_checks.append(f"{check_name}: {reason}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "passport_id": f"spt-{self.run_id}",
            "generated_at": self.timestamp,
            "execution_target": self.execution_env,
            "dimensions": self.dimensions,
            "evidence_references": sorted(list(set(self.evidence_references))),
            "known_limitations": self.limitations,
            "blocked_or_unverified_checks": self.blocked_checks,
        }

    def generate_markdown(self) -> str:
        d = self.to_dict()
        md = [
            f"# Safety Passport: {d['passport_id']}",
            f"**Generated At:** `{d['generated_at']}` | **Execution Target:** `{d['execution_target']}`\n",
            "## Dimension Evaluations\n",
        ]
        for dim, val in d["dimensions"].items():
            md.append(f"### {dim.capitalize()}")
            md.append(f"- **Description:** {val.get('description', '')}")
            for k, v in val.items():
                if k != "description":
                    md.append(f"- **{k}:** `{v}`")
            md.append("")

        md.append("## Evidence References")
        for ref in d["evidence_references"]:
            md.append(f"- `{ref}`")
        md.append("")

        md.append("## Known Limitations & Blocked Checks")
        for b in d["blocked_or_unverified_checks"]:
            md.append(f"- ⚠️ **Blocked:** {b}")
        for l in d["known_limitations"]:
            md.append(f"- ℹ️ **Limitation:** {l}")

        return "\n".join(md)
