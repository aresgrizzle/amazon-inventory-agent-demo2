from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import text

from backend.app.core.database import engine
from backend.app.schemas.inventory_schema import DashboardSummary


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _columns(table_name: str) -> set[str]:
    query = text(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(query, {"table_name": table_name}).mappings().all()
    return {str(row["COLUMN_NAME"]) for row in rows}


def _analysis_summary_fields() -> str:
    analysis_columns = _columns("inventory_agent_analysis")
    task_columns = _columns("inventory_agent_tasks")

    estimated_lost_revenue = (
        "(SELECT COALESCE(SUM(estimated_lost_revenue), 0) FROM inventory_agent_analysis)"
        if "estimated_lost_revenue" in analysis_columns
        else "0"
    )
    high_impact_task_count = (
        """
        (SELECT COUNT(*)
         FROM inventory_agent_tasks
         WHERE task_status = 'pending'
           AND (impact_level = 'high' OR COALESCE(estimated_impact_value, 0) >= 5000))
        """
        if {"impact_level", "estimated_impact_value"}.issubset(task_columns)
        else "0"
    )
    avg_decision_confidence = (
        "(SELECT AVG(decision_confidence) FROM inventory_agent_analysis)"
        if "decision_confidence" in analysis_columns
        else "NULL"
    )
    stockout_risk_score_avg = (
        "(SELECT AVG(stockout_risk_score) FROM inventory_agent_analysis)"
        if "stockout_risk_score" in analysis_columns
        else "NULL"
    )
    overstock_risk_score_avg = (
        "(SELECT AVG(overstock_risk_score) FROM inventory_agent_analysis)"
        if "overstock_risk_score" in analysis_columns
        else "NULL"
    )

    return f"""
            {estimated_lost_revenue} AS estimated_lost_revenue_total,
            {high_impact_task_count} AS high_impact_task_count,
            {avg_decision_confidence} AS avg_decision_confidence,
            {stockout_risk_score_avg} AS stockout_risk_score_avg,
            {overstock_risk_score_avg} AS overstock_risk_score_avg
    """


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary() -> DashboardSummary:
    query = text(
        f"""
        SELECT
            (SELECT COUNT(*) FROM amazon_product_master WHERE is_deleted = 0) AS total_skus,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE stockout_risk_level = 'critical') AS critical_stockout_count,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE stockout_risk_level = 'high') AS high_stockout_count,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE overstock_risk_level = 'high') AS overstock_high_count,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE data_quality_status <> 'complete') AS data_missing_count,
            (SELECT COUNT(*) FROM inventory_agent_tasks WHERE task_status = 'pending') AS pending_task_count,
            (SELECT COUNT(*) FROM inventory_agent_tasks) AS total_tasks,
            {_analysis_summary_fields()}
        """
    )
    with engine.connect() as connection:
        row = connection.execute(query).mappings().one()
    return DashboardSummary(**dict(row))
