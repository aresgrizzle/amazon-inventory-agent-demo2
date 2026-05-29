from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from backend.app.core.database import engine
from backend.app.schemas.inventory_schema import InventoryAnalysisItem


router = APIRouter(prefix="/api/inventory", tags=["inventory"])

ANALYSIS_FIELDS = """
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
    data_quality_status,
    created_at
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
        clauses.append("stockout_risk_level = :stockout_risk_level")
        params["stockout_risk_level"] = stockout_risk_level
    if overstock_risk_level:
        clauses.append("overstock_risk_level = :overstock_risk_level")
        params["overstock_risk_level"] = overstock_risk_level
    if data_quality_status:
        clauses.append("data_quality_status = :data_quality_status")
        params["data_quality_status"] = data_quality_status
    if seller_sku:
        clauses.append("seller_sku LIKE :seller_sku")
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
        SELECT {ANALYSIS_FIELDS}
        FROM inventory_agent_analysis
        {where_sql}
        ORDER BY seller_sku
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(query, params).mappings().all()
    return [InventoryAnalysisItem(**dict(row)) for row in rows]


@router.get("/analysis/{seller_sku}", response_model=InventoryAnalysisItem)
def get_inventory_analysis_detail(seller_sku: str) -> InventoryAnalysisItem:
    query = text(
        f"""
        SELECT {ANALYSIS_FIELDS}
        FROM inventory_agent_analysis
        WHERE seller_sku = :seller_sku
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """
    )
    with engine.connect() as connection:
        row = connection.execute(query, {"seller_sku": seller_sku}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail="Analysis result not found")
    return InventoryAnalysisItem(**dict(row))
