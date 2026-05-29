from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from fastapi import APIRouter

from backend.app.repositories.analysis_repository import clear_analysis
from backend.app.repositories.task_repository import clear_tasks
from backend.app.schemas.inventory_schema import AgentRunResponse
from backend.app.services.inventory_analysis_service import analyze_all_skus
from backend.app.services.task_generation_service import generate_tasks


router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/run-inventory-analysis", response_model=AgentRunResponse)
def run_inventory_analysis() -> AgentRunResponse:
    analysis_batch_id = str(uuid4())
    analysis_datetime = datetime.utcnow()

    clear_analysis()
    clear_tasks()
    analysis_results = analyze_all_skus(
        analysis_batch_id=analysis_batch_id,
        analysis_datetime=analysis_datetime,
    )
    tasks = generate_tasks(analysis_results)

    return AgentRunResponse(
        success=True,
        analyzed_skus=len(analysis_results),
        generated_tasks=len(tasks),
        message="Inventory analysis completed successfully",
    )
