from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional

import pandas as pd

from backend.app.repositories import analysis_repository
from backend.app.repositories.config_repository import get_replenishment_configs
from backend.app.repositories.inventory_repository import get_latest_inventory_snapshots
from backend.app.repositories.product_repository import get_all_products
from backend.app.repositories.sales_repository import get_latest_sales_summaries
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
)


KEY_COLUMNS = ["seller_id", "marketplace_id", "seller_sku"]


def _is_missing(value: Any) -> bool:
    return value is None or pd.isna(value)


def _value(row: Optional[pd.Series], column: str, default: Any = None) -> Any:
    if row is None or column not in row or _is_missing(row[column]):
        return default
    return row[column]


def _float_value(row: Optional[pd.Series], column: str, default: float = 0.0) -> float:
    value = _value(row, column, default)
    return default if _is_missing(value) else float(value)


def _int_value(row: Optional[pd.Series], column: str, default: int = 0) -> int:
    value = _value(row, column, default)
    return default if _is_missing(value) else int(value)


def _optional_int(row: Optional[pd.Series], column: str) -> Optional[int]:
    value = _value(row, column)
    return None if _is_missing(value) else int(value)


def _optional_date(value: Any) -> Optional[date]:
    if _is_missing(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if hasattr(value, "date"):
        return value.date()
    return value


def _index_by_sku(df: pd.DataFrame) -> dict[tuple[str, str, str], pd.Series]:
    if df.empty:
        return {}
    return {
        (row["seller_id"], row["marketplace_id"], row["seller_sku"]): row
        for _, row in df.iterrows()
    }


def _replenishment_urgency(stockout_risk_level: str) -> str:
    if stockout_risk_level == "critical":
        return "urgent"
    if stockout_risk_level == "high":
        return "high"
    if stockout_risk_level == "medium":
        return "normal"
    return "none"


def _confidence_score(data_quality_status: str, avg_daily_sales_7d: float) -> float:
    if data_quality_status == "complete":
        return 95.0 if avg_daily_sales_7d > 0 else 75.0
    if data_quality_status == "missing_sales":
        return 50.0
    if data_quality_status == "missing_config":
        return 40.0
    if data_quality_status in {"invalid_sales", "invalid_config"}:
        return 35.0
    return 20.0


def analyze_all_skus(
    analysis_batch_id: str,
    analysis_datetime: Optional[datetime] = None,
) -> list[dict[str, Any]]:
    analysis_datetime = analysis_datetime or datetime.utcnow()
    analysis_date = analysis_datetime.date()

    print("Loading products...")
    products = get_all_products()
    print(f"{len(products)} SKUs loaded")

    inventory_by_sku = _index_by_sku(get_latest_inventory_snapshots())
    sales_by_sku = _index_by_sku(get_latest_sales_summaries())
    config_by_sku = _index_by_sku(get_replenishment_configs())

    results: list[dict[str, Any]] = []

    for _, product in products.iterrows():
        key = tuple(product[column] for column in KEY_COLUMNS)
        seller_sku = product["seller_sku"]
        print(f"Analyzing SKU: {seller_sku}")

        inventory = inventory_by_sku.get(key)
        sales = sales_by_sku.get(key)
        config = config_by_sku.get(key)

        has_inventory = inventory is not None
        has_sales = sales is not None
        has_config = config is not None

        fulfillable_quantity = _int_value(inventory, "fulfillable_quantity")
        total_quantity = _int_value(inventory, "total_quantity")
        inbound_shipped_quantity = _int_value(inventory, "inbound_shipped_quantity")
        inbound_receiving_quantity = _int_value(inventory, "inbound_receiving_quantity")
        total_unfulfillable_quantity = _int_value(inventory, "total_unfulfillable_quantity")
        avg_daily_sales_7d = _float_value(sales, "avg_daily_sales_7d")
        avg_daily_sales_30d = _float_value(sales, "avg_daily_sales_30d")
        safety_stock_days = _int_value(config, "safety_stock_days")
        target_stock_days = _int_value(config, "target_stock_days")
        total_replenishment_days = _value(config, "total_replenishment_days")
        carton_quantity = _value(config, "carton_quantity")

        data_quality_status = judge_data_quality(
            has_inventory=has_inventory,
            has_sales=has_sales,
            has_config=has_config,
            avg_daily_sales_7d=avg_daily_sales_7d,
            avg_daily_sales_30d=avg_daily_sales_30d,
            total_replenishment_days=total_replenishment_days,
        )

        daily_sales = calculate_daily_sales_for_risk(avg_daily_sales_7d, avg_daily_sales_30d)
        available_days = calculate_available_days(fulfillable_quantity, daily_sales)
        total_cover_days = calculate_total_cover_days(total_quantity, avg_daily_sales_30d)
        effective_inbound_quantity = calculate_effective_inbound_quantity(
            inbound_shipped_quantity,
            inbound_receiving_quantity,
        )
        inbound_cover_days = calculate_total_cover_days(
            effective_inbound_quantity,
            avg_daily_sales_30d,
        )
        estimated_stockout_date = calculate_estimated_stockout_date(
            analysis_date,
            available_days,
        )
        stockout_risk_level = judge_stockout_risk(
            fulfillable_quantity,
            available_days,
            safety_stock_days,
            total_replenishment_days,
        )
        overstock_risk_level = judge_overstock_risk(
            total_quantity,
            avg_daily_sales_30d,
            total_cover_days,
        )
        recommended_replenishment_quantity = calculate_recommended_replenishment_quantity(
            target_stock_days,
            avg_daily_sales_30d,
            fulfillable_quantity,
            effective_inbound_quantity,
            carton_quantity,
        )
        recommended_action = get_recommended_action(
            stockout_risk_level,
            overstock_risk_level,
            recommended_replenishment_quantity,
            data_quality_status,
        )
        need_manual_approval = judge_need_manual_approval(
            recommended_action,
            recommended_replenishment_quantity,
        )
        action_reason = build_action_reason(
            seller_sku,
            available_days,
            stockout_risk_level,
            overstock_risk_level,
            recommended_replenishment_quantity,
        )

        row = {
            "analysis_batch_id": analysis_batch_id,
            "seller_id": product["seller_id"],
            "marketplace_id": product["marketplace_id"],
            "seller_sku": seller_sku,
            "asin": product["asin"],
            "analysis_date": analysis_date,
            "inventory_snapshot_id": _optional_int(inventory, "id"),
            "sales_summary_id": _optional_int(sales, "id"),
            "replenishment_config_id": _optional_int(config, "id"),
            "fulfillable_quantity": fulfillable_quantity,
            "total_quantity": total_quantity,
            "effective_inbound_quantity": effective_inbound_quantity,
            "avg_daily_sales_7d": avg_daily_sales_7d,
            "avg_daily_sales_30d": avg_daily_sales_30d,
            "available_days": available_days,
            "total_cover_days": total_cover_days,
            "inbound_cover_days": inbound_cover_days,
            "total_replenishment_days": None
            if _is_missing(total_replenishment_days)
            else int(total_replenishment_days),
            "safety_stock_days": safety_stock_days if has_config else None,
            "estimated_stockout_date": _optional_date(estimated_stockout_date),
            "stockout_risk_level": stockout_risk_level,
            "overstock_risk_level": overstock_risk_level,
            "replenishment_urgency": _replenishment_urgency(stockout_risk_level),
            "recommended_replenishment_quantity": recommended_replenishment_quantity,
            "recommended_replenishment_date": None,
            "recommended_action": recommended_action,
            "action_reason": action_reason,
            "risk_reason": action_reason,
            "need_manual_approval": need_manual_approval,
            "confidence_score": _confidence_score(data_quality_status, avg_daily_sales_7d),
            "data_quality_status": data_quality_status,
            "total_unfulfillable_quantity": total_unfulfillable_quantity,
        }
        row["id"] = analysis_repository.insert_analysis(row)
        results.append(row)

    return results
