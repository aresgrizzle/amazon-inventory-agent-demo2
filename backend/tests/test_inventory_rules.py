from datetime import date

from backend.app.utils.risk_rules import (
    build_action_reason,
    calculate_available_days,
    calculate_daily_sales_for_risk,
    calculate_effective_inbound_quantity,
    calculate_estimated_stockout_date,
    calculate_recommended_replenishment_quantity,
    calculate_total_cover_days,
    get_recommended_action,
    judge_data_quality,
    judge_need_manual_approval,
    judge_overstock_risk,
    judge_stockout_risk,
    round_up_to_carton,
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
    assert (
        get_recommended_action("critical", "low", 100, "missing_sales")
        == "complete_missing_data"
    )
    assert get_recommended_action("critical", "low", 100, "complete") == "replenish_now"
    assert get_recommended_action("high", "low", 100, "complete") == "replenish_now"
    assert get_recommended_action("medium", "low", 0, "complete") == "prepare_replenishment"
    assert (
        get_recommended_action("low", "high", 0, "complete")
        == "clearance_or_reduce_replenishment"
    )
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
    assert "12.35 天" in reason
    assert "断货风险为 high" in reason
    assert "滞销风险为 low" in reason
    assert "建议补货数量为 120" in reason
