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
    "stockout_risk_score",
    "overstock_risk_score",
    "estimated_lost_revenue",
    "decision_confidence",
]


def _existing_columns(table_name: str) -> set[str]:
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


def _available_analysis_columns() -> list[str]:
    existing = _existing_columns("inventory_agent_analysis")
    return [column for column in ANALYSIS_COLUMNS if column in existing]


def _select_column(
    table_alias: str,
    table_columns: set[str],
    column_name: str,
    output_name: str | None = None,
    default_sql: str = "NULL",
) -> str:
    alias = output_name or column_name
    if column_name in table_columns:
        return f"{table_alias}.{column_name} AS {alias}"
    return f"{default_sql} AS {alias}"


def _enriched_analysis_fields() -> str:
    analysis_columns = _existing_columns("inventory_agent_analysis")
    product_columns = _existing_columns("amazon_product_master")
    sales_columns = _existing_columns("amazon_sales_summary")
    config_columns = _existing_columns("inventory_replenishment_config")

    sales_7d_expr = (
        "s.sales_7d AS sales_7d"
        if "sales_7d" in sales_columns
        else "COALESCE(s.sales_units_7d, 0) AS sales_7d"
    )
    sales_30d_expr = (
        "s.sales_30d AS sales_30d"
        if "sales_30d" in sales_columns
        else "COALESCE(s.sales_units_30d, 0) AS sales_30d"
    )
    lead_time_expr = (
        "c.total_replenishment_lead_time_days AS total_replenishment_lead_time_days"
        if "total_replenishment_lead_time_days" in config_columns
        else "a.total_replenishment_days AS total_replenishment_lead_time_days"
    )
    target_cover_expr = (
        "c.target_cover_days AS target_cover_days"
        if "target_cover_days" in config_columns
        else "c.target_stock_days AS target_cover_days"
    )

    fields = [
        "a.*",
        _select_column("p", product_columns, "current_price", default_sql="0"),
        _select_column("p", product_columns, "landed_cost", default_sql="0"),
        _select_column("p", product_columns, "gross_margin", default_sql="0"),
        sales_7d_expr,
        sales_30d_expr,
        _select_column("s", sales_columns, "sales_trend"),
        _select_column("s", sales_columns, "sales_trend_rate", default_sql="0"),
        lead_time_expr,
        target_cover_expr,
        _select_column("c", config_columns, "moq", default_sql="0"),
        "a.risk_reason AS decision_explanation",
    ]
    for column in [
        "stockout_risk_score",
        "overstock_risk_score",
        "estimated_lost_revenue",
        "decision_confidence",
    ]:
        if column not in analysis_columns:
            fields.append(f"0 AS {column}")
    return ",\n            ".join(fields)


def _enriched_analysis_from_sql() -> str:
    return """
        FROM inventory_agent_analysis a
        LEFT JOIN amazon_product_master p
          ON p.seller_id = a.seller_id
         AND p.marketplace_id = a.marketplace_id
         AND p.seller_sku = a.seller_sku
        LEFT JOIN (
            SELECT *
            FROM (
                SELECT
                    ss.*,
                    ROW_NUMBER() OVER (
                        PARTITION BY seller_id, marketplace_id, seller_sku
                        ORDER BY stat_date DESC, id DESC
                    ) AS row_num
                FROM amazon_sales_summary ss
            ) latest_sales
            WHERE row_num = 1
        ) s
          ON s.seller_id = a.seller_id
         AND s.marketplace_id = a.marketplace_id
         AND s.seller_sku = a.seller_sku
        LEFT JOIN inventory_replenishment_config c
          ON c.seller_id = a.seller_id
         AND c.marketplace_id = a.marketplace_id
         AND c.seller_sku = a.seller_sku
    """


def _summary_extra_fields() -> str:
    analysis_columns = _existing_columns("inventory_agent_analysis")
    task_columns = _existing_columns("inventory_agent_tasks")
    estimated_lost_revenue = (
        "(SELECT COALESCE(SUM(estimated_lost_revenue), 0) FROM inventory_agent_analysis)"
        if "estimated_lost_revenue" in analysis_columns
        else "0"
    )
    high_impact_tasks = (
        """
        (SELECT COUNT(*)
         FROM inventory_agent_tasks
         WHERE task_status = 'pending'
           AND (impact_level = 'high' OR COALESCE(estimated_impact_value, 0) >= 5000))
        """
        if {"impact_level", "estimated_impact_value"}.issubset(task_columns)
        else "0"
    )
    avg_confidence = (
        "(SELECT AVG(decision_confidence) FROM inventory_agent_analysis)"
        if "decision_confidence" in analysis_columns
        else "NULL"
    )
    stockout_score = (
        "(SELECT AVG(stockout_risk_score) FROM inventory_agent_analysis)"
        if "stockout_risk_score" in analysis_columns
        else "NULL"
    )
    overstock_score = (
        "(SELECT AVG(overstock_risk_score) FROM inventory_agent_analysis)"
        if "overstock_risk_score" in analysis_columns
        else "NULL"
    )
    return f"""
            {estimated_lost_revenue} AS estimated_lost_revenue_total,
            {high_impact_tasks} AS high_impact_task_count,
            {avg_confidence} AS avg_decision_confidence,
            {stockout_score} AS stockout_risk_score_avg,
            {overstock_score} AS overstock_risk_score_avg
    """


def clear_analysis() -> None:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE inventory_agent_analysis"))


def insert_analysis(row: dict[str, Any]) -> int:
    columns = _available_analysis_columns()
    values = {column: row.get(column) for column in columns}
    columns_sql = ", ".join(columns)
    params_sql = ", ".join(f":{column}" for column in columns)
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
        f"""
        SELECT
            (SELECT COUNT(*) FROM amazon_product_master WHERE is_deleted = 0) AS total_skus,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE stockout_risk_level = 'critical') AS critical_stockout_count,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE stockout_risk_level = 'high') AS high_stockout_count,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE overstock_risk_level = 'high') AS overstock_high_count,
            (SELECT COUNT(*) FROM inventory_agent_analysis WHERE data_quality_status <> 'complete') AS data_missing_count,
            (SELECT COUNT(*) FROM inventory_agent_tasks WHERE task_status = 'pending') AS pending_task_count,
            (SELECT COUNT(*) FROM inventory_agent_tasks) AS total_tasks,
            {_summary_extra_fields()}
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
        f"""
        SELECT
            {_enriched_analysis_fields()}
        {_enriched_analysis_from_sql()}
        ORDER BY
            CASE a.stockout_risk_level
                WHEN 'critical' THEN 1
                WHEN 'high' THEN 2
                WHEN 'medium' THEN 3
                WHEN 'unknown' THEN 4
                ELSE 5
            END,
            CASE a.overstock_risk_level
                WHEN 'high' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            a.available_days ASC,
            a.seller_sku ASC
        LIMIT :limit
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(query, {"limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def get_latest_analysis_by_sku(seller_sku: str) -> dict[str, Any] | None:
    query = text(
        f"""
        SELECT
            {_enriched_analysis_fields()}
        {_enriched_analysis_from_sql()}
        WHERE a.seller_sku = :seller_sku
        ORDER BY a.created_at DESC, a.id DESC
        LIMIT 1
        """
    )
    with engine.connect() as connection:
        row = connection.execute(query, {"seller_sku": seller_sku}).mappings().first()
    return dict(row) if row else None
