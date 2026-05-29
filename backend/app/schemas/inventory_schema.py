from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class InventoryAnalysisItem(BaseModel):
    seller_sku: str
    asin: str
    fulfillable_quantity: int
    total_quantity: int
    effective_inbound_quantity: int
    avg_daily_sales_7d: float
    avg_daily_sales_30d: float
    available_days: Optional[float]
    total_cover_days: Optional[float]
    estimated_stockout_date: Optional[date]
    stockout_risk_level: str
    overstock_risk_level: str
    recommended_replenishment_quantity: int
    recommended_action: str
    action_reason: Optional[str]
    data_quality_status: str
    created_at: datetime


class DashboardSummary(BaseModel):
    total_skus: int
    critical_stockout_count: int
    high_stockout_count: int
    overstock_high_count: int
    data_missing_count: int
    pending_task_count: int
    total_tasks: int


class AgentRunResponse(BaseModel):
    success: bool
    analyzed_skus: int
    generated_tasks: int
    message: str
