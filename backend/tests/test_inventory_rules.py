from datetime import date, timedelta

from backend.app.utils.risk_rules import (
    build_action_reason,
    calculate_available_days,
    calculate_daily_sales_for_risk,
    calculate_effective_inbound_quantity,
    calculate_estimated_stockout_date,
    calculate_overstock_risk_score,
    calculate_recommended_replenishment_quantity,
    calculate_total_cover_days,
    decision_skill,
    demand_skill,
    get_recommended_action,
    judge_data_quality,
    judge_need_manual_approval,
    judge_overstock_risk,
    judge_stockout_risk,
    profitability_skill,
    replenishment_skill,
    round_up_to_carton,
    stockout_skill,
)


def test_normal_inventory_stockout_risk_is_low() -> None:
    daily_sales = calculate_daily_sales_for_risk(10, 8)
    available_days = calculate_available_days(500, daily_sales)

    assert daily_sales == 10
    assert available_days == 50
    assert judge_stockout_risk(500, available_days, 7, 30) == "low"


def test_stockout_is_critical() -> None:
    assert judge_stockout_risk(0, None, 7, 30) == "critical"


def test_high_stockout_risk_when_available_days_within_replenishment_days() -> None:
    assert judge_stockout_risk(200, 25, 7, 30) == "high"


def test_medium_stockout_risk_when_available_days_within_warning_band() -> None:
    assert judge_stockout_risk(300, 35, 7, 30) == "medium"


def test_no_sales_returns_unknown_stockout_risk() -> None:
    daily_sales = calculate_daily_sales_for_risk(0, 0)
    available_days = calculate_available_days(100, daily_sales)

    assert daily_sales == 0
    assert available_days is None
    assert judge_stockout_risk(100, available_days, 7, 30) == "unknown"


def test_overstock_high_when_total_cover_days_at_least_180() -> None:
    total_cover_days = calculate_total_cover_days(1000, 5)

    assert total_cover_days == 200
    assert judge_overstock_risk(1000, 5, total_cover_days) == "high"


def test_overstock_high_when_inventory_exists_without_sales() -> None:
    assert judge_overstock_risk(500, 0, None) == "high"


def test_replenishment_quantity_rounds_up_to_carton() -> None:
    effective_inbound = calculate_effective_inbound_quantity(50, 30)
    quantity = calculate_recommended_replenishment_quantity(
        target_stock_days=45,
        avg_daily_sales_30d=10,
        fulfillable_quantity=100,
        effective_inbound_quantity=effective_inbound,
        carton_quantity=24,
    )

    assert effective_inbound == 80
    assert quantity == 288
    assert round_up_to_carton(25, 24) == 48


def test_data_quality_missing_cases() -> None:
    assert judge_data_quality(False, True, True, 5, 5, 30) == "missing_inventory"
    assert judge_data_quality(True, False, True, 5, 5, 30) == "missing_sales"
    assert judge_data_quality(True, True, False, 5, 5, 30) == "missing_config"


def test_data_quality_invalid_sales() -> None:
    assert judge_data_quality(True, True, True, -1, 5, 30) == "invalid_sales"


def test_data_quality_invalid_config() -> None:
    assert judge_data_quality(True, True, True, 5, 5, -1) == "invalid_config"


def test_recommended_action_priority() -> None:
    assert get_recommended_action("critical", "low", 100, "missing_sales") == "complete_missing_data"
    assert get_recommended_action("critical", "low", 100, "complete") == "replenish_now"
    assert get_recommended_action("high", "low", 100, "complete") == "replenish_now"
    assert get_recommended_action("medium", "low", 0, "complete") == "prepare_replenishment"
    assert get_recommended_action("low", "high", 0, "complete") == "clearance_or_reduce_replenishment"
    assert get_recommended_action("low", "low", 0, "complete") == "keep_monitoring"


def test_manual_approval_rules() -> None:
    assert judge_need_manual_approval("replenish_now", 10) is True
    assert judge_need_manual_approval("clearance_or_reduce_replenishment", 0) is True
    assert judge_need_manual_approval("keep_monitoring", 500) is True
    assert judge_need_manual_approval("keep_monitoring", 499) is False


def test_estimated_stockout_date_uses_floor_available_days() -> None:
    assert calculate_estimated_stockout_date(date(2026, 5, 27), 7.9) == date(2026, 6, 3)
    assert calculate_estimated_stockout_date(date(2026, 5, 27), None) is None


def test_action_reason_contains_required_business_fields() -> None:
    reason = build_action_reason("SKU-001", 12.345, "high", "low", 120)

    assert "SKU-001" in reason
    assert "high" in reason
    assert "low" in reason
    assert "120" in reason


def test_demand_skill_detects_rising_sales() -> None:
    result = demand_skill(sales_7d=120, sales_30d=300, sales_trend="rising", sales_trend_rate=0.25)

    assert result["demand_signal"] == "rising"
    assert result["demand_score"] > 70


def test_stockout_skill_scores_low_inventory_with_rising_sales_as_critical() -> None:
    result = stockout_skill(
        fulfillable_quantity=5,
        reserved_quantity=2,
        avg_daily_sales_7d=10,
        avg_daily_sales_30d=8,
        available_days=0.5,
        inbound_eta_date=None,
        total_replenishment_lead_time_days=30,
        safety_stock_days=7,
        sales_trend="rising",
        current_price=30,
        today=date(2026, 6, 7),
    )

    assert result["stockout_risk_level"] == "critical"
    assert result["stockout_risk_score"] >= 95
    assert result["estimated_lost_revenue"] > 0


def test_stockout_skill_reduces_risk_when_inbound_arrives_before_stockout() -> None:
    result = stockout_skill(
        fulfillable_quantity=50,
        reserved_quantity=0,
        avg_daily_sales_7d=10,
        avg_daily_sales_30d=10,
        available_days=5,
        inbound_eta_date=date(2026, 6, 10),
        total_replenishment_lead_time_days=30,
        safety_stock_days=7,
        sales_trend="stable",
        current_price=30,
        today=date(2026, 6, 7),
    )

    assert result["stockout_risk_level"] == "high"
    assert result["stockout_risk_score"] < 95


def test_profitability_skill_requires_approval_for_low_margin_replenishment() -> None:
    result = profitability_skill(
        current_price=20,
        purchase_cost=8,
        landed_cost=18,
        gross_margin=0.10,
        recommended_replenishment_quantity=100,
    )

    assert result["profitability_signal"] == "low_margin"
    assert result["approval_required"] is True


def test_replenishment_skill_applies_moq_and_carton_quantity() -> None:
    result = replenishment_skill(
        avg_daily_sales_30d=3,
        sales_trend="stable",
        target_cover_days=30,
        available_quantity=80,
        inbound_quantity=0,
        moq=100,
        carton_quantity=24,
        total_replenishment_lead_time_days=20,
        safety_stock_days=7,
    )

    assert result["recommended_replenishment_quantity"] == 120


def test_decision_skill_lowers_confidence_when_data_is_missing() -> None:
    result = decision_skill(
        demand_result={"demand_signal": "no_sales"},
        stockout_result={
            "stockout_risk_level": "unknown",
            "stockout_risk_score": 40,
            "estimated_lost_revenue": 0,
        },
        overstock_risk_level="unknown",
        overstock_risk_score=40,
        profitability_result={
            "profitability_signal": "unknown",
            "approval_required": False,
        },
        replenishment_result={
            "recommended_replenishment_quantity": 0,
            "recommended_action": "keep_monitoring",
        },
        data_quality_status="missing_sales",
    )

    assert result["recommended_action"] == "complete_missing_data"
    assert result["decision_confidence"] < 50


def test_overstock_score_increases_for_low_margin_slow_moving_inventory() -> None:
    score = calculate_overstock_risk_score(
        overstock_risk_level="high",
        total_cover_days=220,
        avg_daily_sales_30d=2,
        gross_margin=0.10,
    )

    assert score >= 88


def test_stockout_eta_helper_ignores_far_inbound_date() -> None:
    result = stockout_skill(
        fulfillable_quantity=50,
        reserved_quantity=0,
        avg_daily_sales_7d=10,
        avg_daily_sales_30d=10,
        available_days=5,
        inbound_eta_date=date(2026, 7, 20),
        total_replenishment_lead_time_days=30,
        safety_stock_days=7,
        sales_trend="stable",
        current_price=30,
        today=date(2026, 6, 7),
    )

    assert result["stockout_risk_level"] == "critical"
    assert calculate_estimated_stockout_date(date(2026, 6, 7), 5.1) == date(2026, 6, 12)
    assert date(2026, 6, 7) + timedelta(days=5) == date(2026, 6, 12)
