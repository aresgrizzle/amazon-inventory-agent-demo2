from __future__ import annotations

from datetime import date, timedelta
from math import ceil, floor
from typing import Optional


Number = int | float


def _to_float(value: Optional[Number]) -> float:
    if value is None:
        return 0.0
    return float(value)


def calculate_daily_sales_for_risk(
    avg_daily_sales_7d: Optional[Number],
    avg_daily_sales_30d: Optional[Number],
) -> float:
    sales_7d = _to_float(avg_daily_sales_7d)
    if sales_7d > 0:
        return sales_7d

    sales_30d = _to_float(avg_daily_sales_30d)
    if sales_30d > 0:
        return sales_30d

    return 0.0


def calculate_available_days(
    fulfillable_quantity: Optional[Number],
    daily_sales: Optional[Number],
) -> Optional[float]:
    sales = _to_float(daily_sales)
    if sales <= 0:
        return None
    return _to_float(fulfillable_quantity) / sales


def calculate_total_cover_days(
    total_quantity: Optional[Number],
    daily_sales: Optional[Number],
) -> Optional[float]:
    sales = _to_float(daily_sales)
    if sales <= 0:
        return None
    return _to_float(total_quantity) / sales


def calculate_effective_inbound_quantity(
    inbound_shipped_quantity: Optional[int],
    inbound_receiving_quantity: Optional[int],
) -> int:
    return int(_to_float(inbound_shipped_quantity) + _to_float(inbound_receiving_quantity))


def calculate_estimated_stockout_date(
    today: Optional[date],
    available_days: Optional[Number],
) -> Optional[date]:
    if today is None or available_days is None:
        return None
    return today + timedelta(days=floor(_to_float(available_days)))


def judge_stockout_risk(
    fulfillable_quantity: Optional[Number],
    available_days: Optional[Number],
    safety_stock_days: Optional[Number],
    total_replenishment_days: Optional[Number],
) -> str:
    if _to_float(fulfillable_quantity) <= 0:
        return "critical"
    if available_days is None:
        return "unknown"

    available = _to_float(available_days)
    safety_days = _to_float(safety_stock_days)
    replenishment_days = _to_float(total_replenishment_days)

    if available <= safety_days:
        return "critical"
    if available <= replenishment_days:
        return "high"
    if available <= replenishment_days + 7:
        return "medium"
    return "low"


def judge_overstock_risk(
    total_quantity: Optional[Number],
    avg_daily_sales_30d: Optional[Number],
    total_cover_days: Optional[Number],
) -> str:
    total = _to_float(total_quantity)
    if total <= 0:
        return "low"
    if _to_float(avg_daily_sales_30d) <= 0 and total > 0:
        return "high"
    if total_cover_days is None:
        return "unknown"

    cover_days = _to_float(total_cover_days)
    if cover_days >= 180:
        return "high"
    if cover_days >= 90:
        return "medium"
    return "low"


def round_up_to_carton(
    quantity: Optional[Number],
    carton_quantity: Optional[int],
) -> int:
    qty = _to_float(quantity)
    if qty <= 0:
        return 0

    carton = _to_float(carton_quantity)
    if carton <= 0:
        return ceil(qty)

    return int(ceil(qty / carton) * carton)


def calculate_recommended_replenishment_quantity(
    target_stock_days: Optional[Number],
    avg_daily_sales_30d: Optional[Number],
    fulfillable_quantity: Optional[Number],
    effective_inbound_quantity: Optional[Number],
    carton_quantity: Optional[int],
) -> int:
    raw_quantity = (
        _to_float(target_stock_days) * _to_float(avg_daily_sales_30d)
        - _to_float(fulfillable_quantity)
        - _to_float(effective_inbound_quantity)
    )
    if raw_quantity < 0:
        return 0
    return round_up_to_carton(raw_quantity, carton_quantity)


def get_recommended_action(
    stockout_risk_level: Optional[str],
    overstock_risk_level: Optional[str],
    recommended_replenishment_quantity: Optional[int],
    data_quality_status: Optional[str],
) -> str:
    if data_quality_status != "complete":
        return "complete_missing_data"
    if (
        stockout_risk_level in {"critical", "high"}
        and _to_float(recommended_replenishment_quantity) > 0
    ):
        return "replenish_now"
    if stockout_risk_level == "medium":
        return "prepare_replenishment"
    if overstock_risk_level == "high":
        return "clearance_or_reduce_replenishment"
    return "keep_monitoring"


def judge_need_manual_approval(
    recommended_action: Optional[str],
    recommended_replenishment_quantity: Optional[int],
) -> bool:
    if recommended_action in {"replenish_now", "clearance_or_reduce_replenishment"}:
        return True
    return _to_float(recommended_replenishment_quantity) >= 500


def build_action_reason(
    seller_sku: Optional[str],
    available_days: Optional[Number],
    stockout_risk_level: Optional[str],
    overstock_risk_level: Optional[str],
    recommended_replenishment_quantity: Optional[int],
) -> str:
    available_text = "无法计算" if available_days is None else f"{_to_float(available_days):.2f} 天"
    quantity = int(_to_float(recommended_replenishment_quantity))
    sku = seller_sku or "未知 SKU"
    return (
        f"SKU {sku} 当前可售天数为 {available_text}，"
        f"断货风险为 {stockout_risk_level or 'unknown'}，"
        f"滞销风险为 {overstock_risk_level or 'unknown'}，"
        f"建议补货数量为 {quantity}。"
    )


def judge_data_quality(
    has_inventory: Optional[bool],
    has_sales: Optional[bool],
    has_config: Optional[bool],
    avg_daily_sales_7d: Optional[Number],
    avg_daily_sales_30d: Optional[Number],
    total_replenishment_days: Optional[Number],
) -> str:
    if has_inventory is False:
        return "missing_inventory"
    if has_sales is False:
        return "missing_sales"
    if has_config is False:
        return "missing_config"
    if _to_float(avg_daily_sales_7d) < 0 or _to_float(avg_daily_sales_30d) < 0:
        return "invalid_sales"
    if total_replenishment_days is not None and _to_float(total_replenishment_days) < 0:
        return "invalid_config"
    return "complete"
