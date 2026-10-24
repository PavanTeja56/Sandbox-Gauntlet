import os
import shutil
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.config import settings


def check_tool(name: str) -> bool:
    path = shutil.which(name)
    print(f"[{'OK' if path else 'MISSING'}] Tool: {name} -> {path or 'Not in PATH'}")
    return bool(path)


def main():
    print("=== Sandbox Gauntlet System & Setup Diagnostics ===")
    tools = ["python", "git", "docker", "docker-compose", "psql", "pg_isready"]
    for t in tools:
        check_tool(t)

    print("\n--- Configuration Status (No secrets displayed) ---")
    print(f"API_PORT: {settings.API_PORT}")
    print(f"CELESTO_PROVIDER: {settings.CELESTO_PROVIDER}")
    print(f"CELESTO_API_KEY Configured: {bool(settings.CELESTO_API_KEY)}")
    print(f"LLM_MODEL: {settings.LLM_MODEL}")
    print(f"DATABASE_URL Configured: {bool(settings.DATABASE_URL)}")

    # Check for Celesto SDK
    try:
        import celesto
        print("[OK] Celesto SDK imported successfully.")
    except Exception as e:
        print(f"[NOTE] Celesto SDK import note: {e}")

    # Check required reports
    reports = [
        "problem.json", "capabilities.json", "lifecycle.json",
        "reliability.json", "postmortem.md", "containment.json",
        "failure_policy.json", "failure_trace.jsonl", "concurrency.json"
    ]
    print("\n--- Required Reports Check ---")
    for r in reports:
        p = Path("reports") / r
        print(f"[{'OK' if p.exists() else 'MISSING'}] reports/{r}")

    print("\nDiagnostics complete.")


if __name__ == "__main__":
    main()
