import pytest
from app.agent.tasks import compute_expected_benign_metrics, TEN_STEP_WORKFLOW
from app.agent.runner import AgentRunner


def test_benign_task_expected_metrics():
    metrics = compute_expected_benign_metrics()
    assert "avg_cpu_usage_pct" in metrics
    assert "avg_memory_usage_pct" in metrics
    assert "total_request_count" in metrics
    assert metrics["total_request_count"] == 3630
    assert metrics["max_request_count"] == 1450


def test_step_7_recovery_policy_trace(tmp_path):
    trace_file = tmp_path / "failure_trace.jsonl"
    runner = AgentRunner(trace_path=trace_file)
    result = runner.run_step_7_recovery(
        sandbox_name_initial="sbx-testrecov001",
        sandbox_name_fresh="sbx-testrecov002",
        policy="fresh"
    )
    assert result["failed_step"] == 7
    assert result["total_steps"] == 10
    assert result["policy"] == "fresh"

    # Verify trace contains policy_applied event with matching policy
    import json
    with open(trace_file, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    events = [l.get("event") for l in lines]
    assert "step_failure_injected" in events
    assert "policy_applied" in events

    policy_applied_events = [l for l in lines if l.get("event") == "policy_applied"]
    assert len(policy_applied_events) >= 1
    assert policy_applied_events[0]["policy"] == "fresh"
