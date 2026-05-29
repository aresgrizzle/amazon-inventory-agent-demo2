from __future__ import annotations

from typing import Any

from sqlalchemy import text

from backend.app.core.database import engine


ANALYSIS_COLUMNS = [
    "analysis_batch_id",
    "seller_id",
    "marketplace_id",
    "seller_sku",
    "asin",
    "analysis_date",
    "inventory_snapshot_id",
    "sales_summary_id",
    "replenishment_config_id",
    "fulfillable_quantity",
    "total_quantity",
    "effective_inbound_quantity",
    "avg_daily_sales_7d",
    "avg_daily_sales_30d",
    "available_days",
    "total_cover_days",
    "inbound_cover_days",
    "total_replenishment_days",
    "safety_stock_days",
    "estimated_stockout_date",
    "stockout_risk_level",
    "overstock_risk_level",
    "replenishment_urgency",
    "recommended_replenishment_quantity",
    "recommended_replenishment_date",
    "recommended_action",
    "action_reason",
    "risk_reason",
    "need_manual_approval",
    "confidence_score",
    "data_quality_status",
]


def clear_analysis() -> None:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE inventory_agent_analysis"))


def insert_analysis(row: dict[str, Any]) -> int:
    values = {column: row.get(column) for column in ANALYSIS_COLUMNS}
    columns_sql = ", ".join(ANALYSIS_COLUMNS)
    params_sql = ", ".join(f":{column}" for column in ANALYSIS_COLUMNS)
    query = text(
        f"""
        INSERT INTO inventory_agent_analysis ({columns_sql})
        VALUES ({params_sql})
        """
    )
    with engine.begin() as connection:
        result = connection.execute(query, values)
        return int(result.lastrowid)
