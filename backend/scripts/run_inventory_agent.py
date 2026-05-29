from __future__ import annotations

import sys
import warnings
from datetime import datetime
from pathlib import Path
from uuid import uuid4


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.app.repositories.analysis_repository import clear_analysis  # noqa: E402
from backend.app.repositories.task_repository import clear_tasks  # noqa: E402
from backend.app.services.inventory_analysis_service import analyze_all_skus  # noqa: E402
from backend.app.services.task_generation_service import generate_tasks  # noqa: E402


def main() -> None:
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    analysis_batch_id = str(uuid4())
    analysis_datetime = datetime.utcnow()

    print("========== INVENTORY AGENT START ==========")
    print(f"Analysis batch id: {analysis_batch_id}")

    clear_analysis()
    clear_tasks()

    analysis_results = analyze_all_skus(
        analysis_batch_id=analysis_batch_id,
        analysis_datetime=analysis_datetime,
    )
    tasks = generate_tasks(analysis_results)

    critical_high_count = sum(
        1
        for row in analysis_results
        if row["stockout_risk_level"] in {"critical", "high"}
    )
    high_overstock_count = sum(
        1 for row in analysis_results if row["overstock_risk_level"] == "high"
    )

    print("========== ANALYSIS SUMMARY ==========")
    print(f"Total analyzed SKUs: {len(analysis_results)}")
    print(f"Critical/high stockout SKUs: {critical_high_count}")
    print(f"High overstock SKUs: {high_overstock_count}")
    print(f"Generated tasks: {len(tasks)}")
    print("========== INVENTORY AGENT SUCCESS ==========")


if __name__ == "__main__":
    main()
