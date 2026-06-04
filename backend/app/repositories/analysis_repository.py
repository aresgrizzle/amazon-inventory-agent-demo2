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


def get_dashboard_summary_context() -> dict[str, Any]:
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
    return dict(row)


def get_risk_distribution() -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            stockout_risk_level,
            overstock_risk_level,
            data_quality_status,
            COUNT(*) AS sku_count
        FROM inventory_agent_analysis
        GROUP BY stockout_risk_level, overstock_risk_level, data_quality_status
        ORDER BY sku_count DESC
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(query).mappings().all()
    return [dict(row) for row in rows]


def get_top_risk_skus(limit: int = 10) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            seller_sku,
            asin,
            fulfillable_quantity,
            total_quantity,
            effective_inbound_quantity,
            avg_daily_sales_7d,
            avg_daily_sales_30d,
            available_days,
            total_cover_days,
            estimated_stockout_date,
            stockout_risk_level,
            overstock_risk_level,
            recommended_replenishment_quantity,
            recommended_action,
            action_reason,
            data_quality_status
        FROM inventory_agent_analysis
        ORDER BY
            CASE stockout_risk_level
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'unknown' THEN 4
                ELSE 5
            END,
            CASE overstock_risk_level
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            available_days ASC,
            seller_sku ASC
        LIMIT :limit
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(query, {"limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def get_latest_analysis_by_sku(seller_sku: str) -> dict[str, Any] | None:
    query = text(
        """
        SELECT
            seller_sku,
            asin,
            fulfillable_quantity,
            total_quantity,
            effective_inbound_quantity,
            avg_daily_sales_7d,
            avg_daily_sales_30d,
            available_days,
            total_cover_days,
            inbound_cover_days,
            total_replenishment_days,
            safety_stock_days,
            estimated_stockout_date,
            stockout_risk_level,
            overstock_risk_level,
            replenishment_urgency,
            recommended_replenishment_quantity,
            recommended_replenishment_date,
            recommended_action,
            action_reason,
            risk_reason,
            need_manual_approval,
            confidence_score,
            data_quality_status,
            created_at
        FROM inventory_agent_analysis
        WHERE seller_sku = :seller_sku
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
    )
    with engine.connect() as connection:
        row = connection.execute(query, {"seller_sku": seller_sku}).mappings().first()
    return dict(row) if row else None
