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
    current_price: Optional[float] = None
    landed_cost: Optional[float] = None
    gross_margin: Optional[float] = None
    sales_7d: Optional[int] = None
    sales_30d: Optional[int] = None
    sales_trend: Optional[str] = None
    sales_trend_rate: Optional[float] = None
    total_replenishment_lead_time_days: Optional[int] = None
    target_cover_days: Optional[int] = None
    moq: Optional[int] = None
    stockout_risk_score: Optional[float] = None
    overstock_risk_score: Optional[float] = None
    estimated_lost_revenue: Optional[float] = None
    decision_confidence: Optional[float] = None
    decision_explanation: Optional[str] = None


class DashboardSummary(BaseModel):
    total_skus: int
    critical_stockout_count: int
    high_stockout_count: int
    overstock_high_count: int
    data_missing_count: int
    pending_task_count: int
    total_tasks: int
    estimated_lost_revenue_total: float = 0.0
    high_impact_task_count: int = 0
    avg_decision_confidence: Optional[float] = None
    stockout_risk_score_avg: Optional[float] = None
    overstock_risk_score_avg: Optional[float] = None


class AgentRunResponse(BaseModel):
    success: bool
    analyzed_skus: int
    generated_tasks: int
    message: str
