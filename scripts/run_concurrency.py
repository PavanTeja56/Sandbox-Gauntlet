import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.evaluation.engine import EvaluationEngine


def main():
    print("Executing concurrency evaluation across at least 5 sandboxes...")
    engine = EvaluationEngine()
    data = engine.generate_concurrency_report()
    print(f"Generated concurrency report at reports/concurrency.json with {len(data['jobs'])} jobs.")
    print("Breakage notes:", data["breakage_notes"])


if __name__ == "__main__":
    main()
