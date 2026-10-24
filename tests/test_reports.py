import json
import math
import os
import re
from pathlib import Path
import pytest

REPORTS_DIR = Path("reports")
LOGS_DIR = Path("logs")

ALLOWED_CAPABILITY_IDS = {
    "persistence", "snapshots", "celestofs", "browser", "published_ports",
    "network_policy", "safety_hooks", "host_mounts", "coding_agent_preset", "agentor_durable"
}

ALLOWED_ATTACKS = {"prompt_injection_exfil", "destructive_command", "suspicious_package"}
ALLOWED_POLICIES = {"resume", "rollback", "fresh"}


def test_required_files_exist():
    required_paths = [
        "docker-compose.yml",
        "Dockerfile",
        ".env.example",
        "README.md",
        "seeds/01_runs.sql",
        "reports/problem.json",
        "reports/capabilities.json",
        "reports/lifecycle.json",
        "reports/reliability.json",
        "reports/postmortem.md",
        "reports/containment.json",
        "reports/failure_policy.json",
        "reports/failure_trace.jsonl",
        "reports/concurrency.json",
        "logs/commands.jsonl",
        "tests/test_reports.py",
    ]
    for rel_path in required_paths:
        p = Path(rel_path)
        assert p.exists(), f"Required file missing: {rel_path}"


def test_no_live_env_committed():
    # .env.example must exist
    assert Path(".env.example").exists()
    with open(".env.example", "r", encoding="utf-8") as f:
        content = f.read()
    assert "replace-me" in content or "placeholder" in content.lower()


def test_problem_report():
    p = REPORTS_DIR / "problem.json"
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    for k in ["who", "agent_work", "proof_output", "idea_source"]:
        assert k in data, f"Missing key '{k}' in problem.json"

    assert data["idea_source"] in ("idea_bank", "original")
    assert len(data["who"]) >= 40
    assert len(data["agent_work"]) >= 40
    assert len(data["proof_output"]) >= 20


def test_capabilities_report():
    p = REPORTS_DIR / "capabilities.json"
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "capabilities" in data
    caps = data["capabilities"]
    assert len(caps) >= 2, "Must contain at least two capability objects"

    ids = [c["id"] for c in caps]
    assert len(ids) == len(set(ids)), "Capability IDs must be unique"

    for c in caps:
        assert c["id"] in ALLOWED_CAPABILITY_IDS, f"Invalid capability ID: {c['id']}"
        assert len(c["why"]) >= 80, f"Capability {c['id']} 'why' must be at least 80 characters"
        ev_path = Path(c["evidence_path"])
        assert ev_path.exists(), f"Evidence path does not exist: {c['evidence_path']}"


def test_lifecycle_report():
    p = REPORTS_DIR / "lifecycle.json"
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data.get("cleanup_on_success") is True
    assert data.get("cleanup_on_failure") is True
    assert data.get("cleanup_on_interrupt") is True

    names = data.get("sandbox_names", [])
    assert len(names) > 0
    assert len(names) == len(set(names)), "sandbox_names must be unique"

    for name in names:
        assert name.startswith("sbx-")
        suffix = name[4:]
        assert len(suffix) >= 8 and re.match(r"^[a-z0-9]+$", suffix)

    # Confirm each name appears in logs/commands.jsonl or in reports/reliability.json
    commands_log = LOGS_DIR / "commands.jsonl"
    log_names = set()
    if commands_log.exists():
        with open(commands_log, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    log_names.add(json.loads(line).get("sandbox_name"))

    rel_p = REPORTS_DIR / "reliability.json"
    with open(rel_p, "r", encoding="utf-8") as f:
        rel_names = {r["sandbox_name"] for r in json.load(f).get("runs", [])}

    known_names = log_names.union(rel_names)
    for name in names:
        assert name in known_names, f"Sandbox {name} not found in commands.jsonl or reliability.json"


def test_commands_audit_log():
    p = LOGS_DIR / "commands.jsonl"
    assert p.exists()
    lines = []
    with open(p, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                lines.append(json.loads(line))

    assert len(lines) >= 1
    for obj in lines:
        assert "ts" in obj
        assert obj["sandbox_name"].startswith("sbx-")
        assert len(obj["sandbox_name"][4:]) >= 8
        assert obj["command"] and len(obj["command"].strip()) > 0
        assert obj["decision"] in ("allow", "block")
        assert obj["execution_target"] == "celesto_sandbox"


def test_reliability_report_and_calculations():
    p = REPORTS_DIR / "reliability.json"
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    runs = data.get("runs", [])
    run_count = data.get("run_count")
    assert run_count >= 20
    assert run_count == len(runs)

    names = [r["sandbox_name"] for r in runs]
    assert len(names) == len(set(names)), "Reliability sandbox names must be unique"

    for r in runs:
        assert r["fresh"] is True
        assert isinstance(r["success"], bool)
        assert r["wall_clock_s"] >= 0
        assert r["boot_to_ready_s"] >= 0
        assert r["cost_usd"] >= 0
        assert r["sandbox_name"].startswith("sbx-")
        assert len(r["sandbox_name"][4:]) >= 8

    # Arithmetic checks
    successes = sum(1 for r in runs if r["success"])
    calc_success_rate = successes / run_count
    assert abs(data["success_rate"] - calc_success_rate) <= 0.001

    # Wall clock median
    sorted_wall = sorted([r["wall_clock_s"] for r in runs])
    if run_count % 2 == 0:
        idx1 = (run_count // 2) - 1
        idx2 = idx1 + 1
        calc_median_wall = (sorted_wall[idx1] + sorted_wall[idx2]) / 2.0
    else:
        calc_median_wall = sorted_wall[run_count // 2]
    assert abs(data["median_wall_clock_s"] - calc_median_wall) <= 0.001

    # P90: 1-based rank ceil(0.90 * n)
    p90_idx = math.ceil(0.90 * run_count) - 1
    calc_p90 = sorted_wall[p90_idx]
    assert abs(data["p90_wall_clock_s"] - calc_p90) <= 0.001

    # Boot to ready median
    sorted_boot = sorted([r["boot_to_ready_s"] for r in runs])
    if run_count % 2 == 0:
        idx1 = (run_count // 2) - 1
        idx2 = idx1 + 1
        calc_median_boot = (sorted_boot[idx1] + sorted_boot[idx2]) / 2.0
    else:
        calc_median_boot = sorted_boot[run_count // 2]
    assert abs(data["median_boot_to_ready_s"] - calc_median_boot) <= 0.001

    # Total cost
    calc_total_cost = sum(r["cost_usd"] for r in runs)
    assert abs(data["total_cost_usd"] - calc_total_cost) <= 0.01

    # Postmortem check
    postmortem_path = Path(data["postmortem_path"])
    assert postmortem_path.exists()
    with open(postmortem_path, "r", encoding="utf-8") as f:
        pm_content = f.read()
    assert len(pm_content.strip()) >= 200


def test_containment_report():
    p = REPORTS_DIR / "containment.json"
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["attack"] in ALLOWED_ATTACKS
    assert data["blocked"] is True
    assert data["host_untouched"] is True

    evidence_paths = data.get("evidence_paths", [])
    assert len(evidence_paths) >= 1
    for ep in evidence_paths:
        assert Path(ep).exists(), f"Containment evidence path missing: {ep}"


def test_failure_policy_and_trace():
    policy_path = REPORTS_DIR / "failure_policy.json"
    with open(policy_path, "r", encoding="utf-8") as f:
        pdata = json.load(f)

    assert pdata["failed_step"] == 7
    assert pdata["total_steps"] == 10
    assert pdata["policy"] in ALLOWED_POLICIES
    assert len(pdata["rationale"]) >= 200

    trace_path = Path(pdata["trace_path"])
    assert trace_path.exists()

    trace_lines = []
    with open(trace_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                trace_lines.append(json.loads(line))

    # Trace must have a line with event == policy_applied and policy matching
    applied = [l for l in trace_lines if l.get("event") == "policy_applied"]
    assert len(applied) >= 1
    assert applied[0]["policy"] == pdata["policy"]


def test_concurrency_report():
    p = REPORTS_DIR / "concurrency.json"
    with open(p, "r", encoding="utf-8") as f:
        data = json.load(f)

    jobs = data.get("jobs", [])
    assert len(jobs) >= 5

    names = [j["sandbox_name"] for j in jobs]
    assert len(names) == len(set(names)), "Concurrency sandbox names must be unique"

    for j in jobs:
        assert j["sandbox_name"].startswith("sbx-")
        assert len(j["sandbox_name"][4:]) >= 8
        assert j.get("started_at") and len(j["started_at"].strip()) > 0

    assert len(data.get("breakage_notes", "")) >= 40


def test_readme_required_phrases():
    readme_path = Path("README.md")
    assert readme_path.exists()
    with open(readme_path, "r", encoding="utf-8") as f:
        text = f.read()

    required_phrases = [
        "Problem statement",
        "How I used Celesto",
        "Eval report",
        "Containment test",
        "State and failure design",
        "Setup"
    ]
    for phrase in required_phrases:
        assert phrase in text, f"Missing required phrase in README.md: '{phrase}'"
