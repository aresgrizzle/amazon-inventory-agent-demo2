from __future__ import annotations

from datetime import date, timedelta
from math import ceil, floor
from typing import Any, Optional


Number = int | float


def _to_float(value: Optional[Number]) -> float:
    if value is None:
        return 0.0
    return float(value)


def _level_score(level: Optional[str]) -> float:
    return {
        "critical": 95.0,
        "high": 80.0,
        "medium": 55.0,
        "unknown": 40.0,
        "low": 20.0,
    }.get(level or "unknown", 40.0)


def _days_until(today: date, target_date: Any) -> Optional[int]:
    if target_date is None:
        return None
    if hasattr(target_date, "date"):
        target_date = target_date.date()
    if not isinstance(target_date, date):
        return None
    return (target_date - today).days


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


def demand_skill(
    sales_7d: Optional[Number],
    sales_30d: Optional[Number],
    sales_trend: Optional[str],
    sales_trend_rate: Optional[Number],
) -> dict[str, Any]:
    sales_7 = _to_float(sales_7d)
    sales_30 = _to_float(sales_30d)
    rate = _to_float(sales_trend_rate)
    trend = (sales_trend or "").lower()

    if sales_30 <= 0:
        signal = "no_sales"
        score = 0.0
        explanation = "No recent sales were provided, so demand is treated as no_sales."
    elif trend in {"rising", "up"} or rate >= 0.15:
        signal = "rising"
        score = min(100.0, 70.0 + max(rate, 0.0) * 100)
        explanation = "Recent demand is rising, so stockout and replenishment decisions should be more conservative."
    elif trend in {"declining", "down"} or rate <= -0.15:
        signal = "declining"
        score = max(10.0, 45.0 + rate * 100)
        explanation = "Recent demand is declining, so replenishment should avoid creating excess inventory."
    else:
        signal = "stable"
        score = 55.0 if sales_7 > 0 else 35.0
        explanation = "Demand is stable based on the current sales trend signal."

    return {
        "demand_signal": signal,
        "demand_score": round(score, 4),
        "explanation": explanation,
    }


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


def stockout_skill(
    fulfillable_quantity: Optional[Number],
    reserved_quantity: Optional[Number],
    avg_daily_sales_7d: Optional[Number],
    avg_daily_sales_30d: Optional[Number],
    available_days: Optional[Number],
    inbound_eta_date: Any,
    total_replenishment_lead_time_days: Optional[Number],
    safety_stock_days: Optional[Number],
    sales_trend: Optional[str],
    current_price: Optional[Number],
    today: Optional[date] = None,
) -> dict[str, Any]:
    today = today or date.today()
    lead_time = _to_float(total_replenishment_lead_time_days)
    daily_sales = calculate_daily_sales_for_risk(avg_daily_sales_7d, avg_daily_sales_30d)
    level = judge_stockout_risk(
        fulfillable_quantity,
        available_days,
        safety_stock_days,
        total_replenishment_lead_time_days,
    )
    score = _level_score(level)
    trend = (sales_trend or "").lower()
    if trend in {"rising", "up"} and level in {"high", "medium"}:
        score = min(100.0, score + 8.0)

    eta_days = _days_until(today, inbound_eta_date)
    if eta_days is not None and available_days is not None and eta_days <= _to_float(available_days) + 3:
        score = max(20.0, score - 15.0)
        if level == "critical":
            level = "high"
        elif level == "high":
            level = "medium"

    available = 0.0 if available_days is None else _to_float(available_days)
    lost_units = 0
    if daily_sales > 0 and lead_time > available:
        lost_units = ceil((lead_time - available) * daily_sales)
    if _to_float(fulfillable_quantity) <= 0 and daily_sales > 0:
        lost_units = max(lost_units, ceil(lead_time * daily_sales))

    estimated_lost_revenue = round(lost_units * _to_float(current_price), 2)
    reserved = _to_float(reserved_quantity)
    explanation = (
        f"Stockout risk is {level}; fulfillable inventory is {_to_float(fulfillable_quantity):.0f}, "
        f"reserved inventory is {reserved:.0f}, available days are "
        f"{'unknown' if available_days is None else f'{_to_float(available_days):.2f}'}, "
        f"lead time is {lead_time:.0f} days."
    )

    return {
        "stockout_risk_level": level,
        "stockout_risk_score": round(score, 4),
        "estimated_lost_sales_units": int(lost_units),
        "estimated_lost_revenue": estimated_lost_revenue,
        "explanation": explanation,
    }


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


def calculate_overstock_risk_score(
    overstock_risk_level: Optional[str],
    total_cover_days: Optional[Number],
    avg_daily_sales_30d: Optional[Number],
    gross_margin: Optional[Number],
) -> float:
    score = _level_score(overstock_risk_level)
    if total_cover_days is not None and _to_float(total_cover_days) >= 180:
        score = max(score, 88.0)
    if _to_float(avg_daily_sales_30d) <= 0:
        score = max(score, 85.0)
    if _to_float(gross_margin) < 0.15 and overstock_risk_level in {"high", "medium"}:
        score = min(100.0, score + 8.0)
    return round(score, 4)


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


def replenishment_skill(
    avg_daily_sales_30d: Optional[Number],
    sales_trend: Optional[str],
    target_cover_days: Optional[Number],
    available_quantity: Optional[Number],
    inbound_quantity: Optional[Number],
    moq: Optional[int],
    carton_quantity: Optional[int],
    total_replenishment_lead_time_days: Optional[Number],
    safety_stock_days: Optional[Number],
) -> dict[str, Any]:
    trend = (sales_trend or "").lower()
    demand = _to_float(avg_daily_sales_30d)
    target_days = _to_float(target_cover_days)
    if target_days <= 0:
        target_days = _to_float(total_replenishment_lead_time_days) + _to_float(safety_stock_days)
    if trend in {"rising", "up"}:
        target_days *= 1.15
    elif trend in {"declining", "down"}:
        target_days *= 0.8

    raw_quantity = target_days * demand - _to_float(available_quantity) - _to_float(inbound_quantity)
    quantity = round_up_to_carton(max(raw_quantity, 0), carton_quantity)
    minimum_order = int(_to_float(moq))
    if 0 < quantity < minimum_order:
        quantity = round_up_to_carton(minimum_order, carton_quantity)

    action = "replenish_now" if quantity > 0 else "keep_monitoring"
    explanation = (
        f"Recommended quantity is {quantity}, based on target cover days {target_days:.1f}, "
        f"30-day average daily sales {demand:.2f}, available inventory {_to_float(available_quantity):.0f}, "
        f"inbound inventory {_to_float(inbound_quantity):.0f}, MOQ {minimum_order}."
    )

    return {
        "recommended_replenishment_quantity": quantity,
        "recommended_replenishment_days": int(ceil(target_days)) if target_days > 0 else 0,
        "recommended_action": action,
        "explanation": explanation,
    }


def profitability_skill(
    current_price: Optional[Number],
    purchase_cost: Optional[Number],
    landed_cost: Optional[Number],
    gross_margin: Optional[Number],
    recommended_replenishment_quantity: Optional[Number],
) -> dict[str, Any]:
    price = _to_float(current_price)
    cost = _to_float(landed_cost) or _to_float(purchase_cost)
    margin = _to_float(gross_margin)
    if margin == 0 and price > 0:
        margin = (price - cost) / price

    if price <= 0 or cost <= 0:
        signal = "unknown"
        explanation = "Price or cost is missing, so replenishment profitability needs review."
    elif margin < 0:
        signal = "loss"
        explanation = "The SKU appears to be selling below landed cost."
    elif margin < 0.18:
        signal = "low_margin"
        explanation = "Margin is low, so replenishment should require manual review."
    elif margin >= 0.35:
        signal = "high_margin"
        explanation = "Margin is healthy, so replenishment is financially attractive if demand exists."
    else:
        signal = "healthy"
        explanation = "Margin is acceptable for a normal replenishment decision."

    replenishment_value = round(_to_float(recommended_replenishment_quantity) * cost, 2)
    approval_required = signal in {"loss", "low_margin", "unknown"} and _to_float(
        recommended_replenishment_quantity
    ) > 0

    return {
        "profitability_signal": signal,
        "gross_margin": round(margin, 4),
        "recommended_replenishment_value": replenishment_value,
        "approval_required": approval_required,
        "explanation": explanation,
    }


def decision_skill(
    demand_result: dict[str, Any],
    stockout_result: dict[str, Any],
    overstock_risk_level: Optional[str],
    overstock_risk_score: Optional[Number],
    profitability_result: dict[str, Any],
    replenishment_result: dict[str, Any],
    data_quality_status: Optional[str],
) -> dict[str, Any]:
    data_quality = data_quality_status or "complete"
    stockout_level = stockout_result.get("stockout_risk_level", "unknown")
    quantity = _to_float(replenishment_result.get("recommended_replenishment_quantity"))
    profitability_signal = profitability_result.get("profitability_signal", "unknown")

    if data_quality != "complete":
        action = "complete_missing_data"
        final_level = "unknown"
        confidence = 45.0
    elif stockout_level in {"critical", "high"} and quantity > 0:
        action = "replenish_now"
        final_level = stockout_level
        confidence = 88.0
    elif stockout_level == "medium":
        action = "prepare_replenishment"
        final_level = "medium"
        confidence = 78.0
    elif overstock_risk_level == "high":
        action = "clearance_or_reduce_replenishment"
        final_level = "high"
        confidence = 82.0
    else:
        action = "keep_monitoring"
        final_level = "low"
        confidence = 86.0

    if profitability_signal in {"loss", "low_margin", "unknown"} and action == "replenish_now":
        confidence = min(confidence, 70.0)

    approval_required = bool(profitability_result.get("approval_required")) or action in {
        "replenish_now",
        "clearance_or_reduce_replenishment",
    }
    explanation = (
        f"Demand signal is {demand_result.get('demand_signal')}; stockout score is "
        f"{stockout_result.get('stockout_risk_score')}; overstock score is {overstock_risk_score}; "
        f"profitability signal is {profitability_signal}; final action is {action}."
    )

    return {
        "final_risk_level": final_level,
        "recommended_action": action,
        "decision_confidence": round(confidence, 4),
        "approval_required": approval_required,
        "decision_explanation": explanation,
    }


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
