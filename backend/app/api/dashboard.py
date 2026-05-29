from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from backend.app.core.database import engine
from backend.app.schemas.inventory_schema import DashboardSummary


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary() -> DashboardSummary:
    query = text(
        """
        SELECT
            (SELECT COUNT(*) FROM amazon_product_master WHERE is_deleted = 0) AS total_skus,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE stockout_risk_level = 'critical') AS critical_stockout_count,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE stockout_risk_level = 'high') AS high_stockout_count,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE overstock_risk_level = 'high') AS overstock_high_count,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE data_quality_status <> 'complete') AS data_missing_count,
            (SELECT COUNT(*) FROM inventory_agent_tasks WHERE task_status = 'pending') AS pending_task_count,
            (SELECT COUNT(*) FROM inventory_agent_tasks) AS total_tasks
        """
    )
    with engine.connect() as connection:
        row = connection.execute(query).mappings().one()
    return DashboardSummary(**dict(row))
