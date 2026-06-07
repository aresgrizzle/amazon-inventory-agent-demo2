from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from backend.app.core.database import engine
from backend.app.schemas.inventory_schema import InventoryAnalysisItem


router = APIRouter(prefix="/api/inventory", tags=["inventory"])


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


def _inventory_analysis_fields() -> str:
    analysis_columns = _columns("inventory_agent_analysis")
    product_columns = _columns("amazon_product_master")
    sales_columns = _columns("amazon_sales_summary")
    config_columns = _columns("inventory_replenishment_config")

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
        "a.seller_sku",
        "a.asin",
        "a.fulfillable_quantity",
        "a.total_quantity",
        "a.effective_inbound_quantity",
        "a.avg_daily_sales_7d",
        "a.avg_daily_sales_30d",
        "a.available_days",
        "a.total_cover_days",
        "a.estimated_stockout_date",
        "a.stockout_risk_level",
        "a.overstock_risk_level",
        "a.recommended_replenishment_quantity",
        "a.recommended_action",
        "a.action_reason",
        "a.data_quality_status",
        "a.created_at",
        _select_column("p", product_columns, "current_price", default_sql="0"),
        _select_column("p", product_columns, "landed_cost", default_sql="0"),
        _select_column("p", product_columns, "gross_margin", default_sql="0"),
        sales_7d_expr,
        sales_30d_expr,
        _select_column("s", sales_columns, "sales_trend"),
        _select_column("s", sales_columns, "sales_trend_rate", default_sql="0"),
        lead_time_expr,
        target_cover_expr,
        "a.safety_stock_days",
        _select_column("c", config_columns, "moq", default_sql="0"),
        _select_column("a", analysis_columns, "stockout_risk_score", default_sql="0"),
        _select_column("a", analysis_columns, "overstock_risk_score", default_sql="0"),
        _select_column("a", analysis_columns, "estimated_lost_revenue", default_sql="0"),
        _select_column("a", analysis_columns, "decision_confidence", default_sql="0"),
        "a.risk_reason AS decision_explanation",
    ]
    return ",\n    ".join(fields)


def _analysis_from_sql() -> str:
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


def _build_analysis_filters(
    stockout_risk_level: Optional[str],
    overstock_risk_level: Optional[str],
    data_quality_status: Optional[str],
    seller_sku: Optional[str],
) -> tuple[str, dict[str, str]]:
    clauses: list[str] = []
    params: dict[str, str] = {}
    if stockout_risk_level:
        clauses.append("a.stockout_risk_level = :stockout_risk_level")
        params["stockout_risk_level"] = stockout_risk_level
    if overstock_risk_level:
        clauses.append("a.overstock_risk_level = :overstock_risk_level")
        params["overstock_risk_level"] = overstock_risk_level
    if data_quality_status:
        clauses.append("a.data_quality_status = :data_quality_status")
        params["data_quality_status"] = data_quality_status
    if seller_sku:
        clauses.append("a.seller_sku LIKE :seller_sku")
        params["seller_sku"] = f"%{seller_sku}%"

    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params


@router.get("/analysis", response_model=list[InventoryAnalysisItem])
def list_inventory_analysis(
    stockout_risk_level: Optional[str] = Query(default=None),
    overstock_risk_level: Optional[str] = Query(default=None),
    data_quality_status: Optional[str] = Query(default=None),
    seller_sku: Optional[str] = Query(default=None),
) -> list[InventoryAnalysisItem]:
    where_sql, params = _build_analysis_filters(
        stockout_risk_level,
        overstock_risk_level,
        data_quality_status,
        seller_sku,
    )
    query = text(
        f"""
        SELECT {_inventory_analysis_fields()}
        {_analysis_from_sql()}
        {where_sql}
        ORDER BY a.seller_sku
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(query, params).mappings().all()
    return [InventoryAnalysisItem(**dict(row)) for row in rows]


@router.get("/analysis/{seller_sku}", response_model=InventoryAnalysisItem)
def get_inventory_analysis_detail(seller_sku: str) -> InventoryAnalysisItem:
    query = text(
        f"""
        SELECT {_inventory_analysis_fields()}
        {_analysis_from_sql()}
        WHERE a.seller_sku = :seller_sku
        ORDER BY a.created_at DESC, a.id DESC
        LIMIT 1
        """
    )
    with engine.connect() as connection:
        row = connection.execute(query, {"seller_sku": seller_sku}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return InventoryAnalysisItem(**dict(row))
