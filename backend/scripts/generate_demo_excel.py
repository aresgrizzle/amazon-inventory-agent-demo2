from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import pandas as pd


SELLER_ID = "SELLER_DEMO_001"
MARKETPLACE_ID = "ATVPDKIKX0DER"
MARKETPLACE_NAME = "Amazon US"

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"

TODAY = date.today()
SYNC_TIME = datetime.combine(TODAY, datetime.min.time()).replace(hour=9)
SYNC_BATCH_ID = f"SYNC_DEMO_{TODAY:%Y%m%d}"


PRODUCT_MASTER_COLUMNS = [
    "seller_id",
    "marketplace_id",
    "marketplace_name",
    "seller_sku",
    "asin",
    "fn_sku",
    "product_name",
    "brand",
    "product_type",
    "category_name",
    "condition_type",
    "fulfillment_channel",
    "listing_status",
    "lifecycle_stage",
    "launch_date",
    "is_deleted",
]

INVENTORY_SNAPSHOT_COLUMNS = [
    "seller_id",
    "marketplace_id",
    "seller_sku",
    "asin",
    "fn_sku",
    "condition_type",
    "total_quantity",
    "fulfillable_quantity",
    "inbound_working_quantity",
    "inbound_shipped_quantity",
    "inbound_receiving_quantity",
    "total_reserved_quantity",
    "pending_customer_order_quantity",
    "pending_transshipment_quantity",
    "fc_processing_quantity",
    "total_unfulfillable_quantity",
    "total_researching_quantity",
    "amazon_last_updated_time",
    "sync_batch_id",
    "sync_time",
]

SALES_SUMMARY_COLUMNS = [
    "seller_id",
    "marketplace_id",
    "seller_sku",
    "asin",
    "stat_date",
    "sales_units_1d",
    "sales_units_3d",
    "sales_units_7d",
    "sales_units_14d",
    "sales_units_30d",
    "avg_daily_sales_3d",
    "avg_daily_sales_7d",
    "avg_daily_sales_30d",
    "sales_amount_7d",
    "sales_amount_30d",
    "currency",
    "sales_trend",
    "sales_trend_rate",
    "data_source",
]

REPLENISHMENT_CONFIG_COLUMNS = [
    "seller_id",
    "marketplace_id",
    "seller_sku",
    "supplier_name",
    "purchase_lead_time_days",
    "domestic_shipping_days",
    "international_shipping_days",
    "customs_clearance_days",
    "amazon_receiving_days",
    "total_replenishment_days",
    "safety_stock_days",
    "target_stock_days",
    "max_stock_days",
    "moq",
    "carton_quantity",
    "case_pack_quantity",
    "preferred_shipping_method",
    "reorder_point_days",
    "config_status",
]


SCENARIOS = [
    ("normal", "正常库存 SKU", 8),
    ("high_stockout_risk", "高断货风险 SKU", 6),
    ("stockout", "已断货 SKU", 3),
    ("overstock", "滞销 SKU", 5),
    ("large_inbound", "在途库存较多 SKU", 4),
    ("unfulfillable_issue", "不可售异常 SKU", 2),
    ("data_missing", "数据缺失 SKU", 2),
]


def build_sku_plan() -> list[dict]:
    plan = []
    sequence = 1
    for scenario, scenario_name, count in SCENARIOS:
        for index in range(1, count + 1):
            plan.append(
                {
                    "sequence": sequence,
                    "scenario": scenario,
                    "scenario_name": scenario_name,
                    "scenario_index": index,
                    "seller_sku": f"DEMO-{scenario.upper().replace('_', '-')}-{index:02d}",
                    "asin": f"B0DEMO{sequence:04d}",
                    "fn_sku": f"FNSKUDEMO{sequence:04d}",
                }
            )
            sequence += 1
    return plan


def product_row(item: dict) -> dict:
    sequence = item["sequence"]
    scenario_title = item["scenario_name"].replace(" SKU", "")
    return {
        "seller_id": SELLER_ID,
        "marketplace_id": MARKETPLACE_ID,
        "marketplace_name": MARKETPLACE_NAME,
        "seller_sku": item["seller_sku"],
        "asin": item["asin"],
        "fn_sku": item["fn_sku"],
        "product_name": f"Demo {scenario_title} Product {item['scenario_index']:02d}",
        "brand": "DemoBrand",
        "product_type": "home_storage",
        "category_name": "Home & Kitchen",
        "condition_type": "New",
        "fulfillment_channel": "FBA",
        "listing_status": "Active",
        "lifecycle_stage": lifecycle_stage(item["scenario"]),
        "launch_date": TODAY - timedelta(days=90 + sequence * 7),
        "is_deleted": 0,
    }


def lifecycle_stage(scenario: str) -> str:
    if scenario == "overstock":
        return "mature"
    if scenario in {"high_stockout_risk", "stockout"}:
        return "growth"
    if scenario == "data_missing":
        return "launch"
    return "stable"


def inventory_row(item: dict) -> dict:
    scenario = item["scenario"]
    index = item["scenario_index"]

    values = {
        "normal": {
            "fulfillable": 180 + index * 12,
            "working": 20,
            "shipped": 18,
            "receiving": 8,
            "reserved": 6,
            "unfulfillable": 1,
            "researching": 0,
        },
        "high_stockout_risk": {
            "fulfillable": 10 + index * 2,
            "working": 8,
            "shipped": 5,
            "receiving": 2,
            "reserved": 4,
            "unfulfillable": 0,
            "researching": 0,
        },
        "stockout": {
            "fulfillable": 0,
            "working": 3,
            "shipped": 0,
            "receiving": 0,
            "reserved": 0,
            "unfulfillable": 0,
            "researching": 0,
        },
        "overstock": {
            "fulfillable": 520 + index * 60,
            "working": 0,
            "shipped": 0,
            "receiving": 0,
            "reserved": 3,
            "unfulfillable": 2,
            "researching": 0,
        },
        "large_inbound": {
            "fulfillable": 70 + index * 8,
            "working": 40,
            "shipped": 180 + index * 20,
            "receiving": 90 + index * 15,
            "reserved": 5,
            "unfulfillable": 1,
            "researching": 0,
        },
        "unfulfillable_issue": {
            "fulfillable": 75 + index * 10,
            "working": 5,
            "shipped": 8,
            "receiving": 4,
            "reserved": 5,
            "unfulfillable": 55 + index * 15,
            "researching": 8,
        },
        "data_missing": {
            "fulfillable": 35 + index * 8,
            "working": 0,
            "shipped": 0,
            "receiving": 0,
            "reserved": 2,
            "unfulfillable": 0,
            "researching": 0,
        },
    }[scenario]

    total_quantity = (
        values["fulfillable"]
        + values["working"]
        + values["shipped"]
        + values["receiving"]
        + values["reserved"]
        + values["unfulfillable"]
        + values["researching"]
    )

    return {
        "seller_id": SELLER_ID,
        "marketplace_id": MARKETPLACE_ID,
        "seller_sku": item["seller_sku"],
        "asin": item["asin"],
        "fn_sku": item["fn_sku"],
        "condition_type": "New",
        "total_quantity": total_quantity,
        "fulfillable_quantity": values["fulfillable"],
        "inbound_working_quantity": values["working"],
        "inbound_shipped_quantity": values["shipped"],
        "inbound_receiving_quantity": values["receiving"],
        "total_reserved_quantity": values["reserved"],
        "pending_customer_order_quantity": min(values["reserved"], 4),
        "pending_transshipment_quantity": max(values["reserved"] - 4, 0),
        "fc_processing_quantity": values["receiving"] // 3,
        "total_unfulfillable_quantity": values["unfulfillable"],
        "total_researching_quantity": values["researching"],
        "amazon_last_updated_time": SYNC_TIME - timedelta(hours=2),
        "sync_batch_id": SYNC_BATCH_ID,
        "sync_time": SYNC_TIME,
    }


def sales_row(item: dict) -> dict | None:
    if item["scenario"] == "data_missing" and item["scenario_index"] == 1:
        return None

    scenario = item["scenario"]
    index = item["scenario_index"]
    units_30d = {
        "normal": 145 + index * 8,
        "high_stockout_risk": 300 + index * 25,
        "stockout": 95 + index * 12,
        "overstock": 4 + index,
        "large_inbound": 115 + index * 12,
        "unfulfillable_issue": 95 + index * 10,
        "data_missing": 55,
    }[scenario]

    units_14d = round(units_30d * trend_ratio(scenario, 14))
    units_7d = round(units_30d * trend_ratio(scenario, 7))
    units_3d = round(units_30d * trend_ratio(scenario, 3))
    units_1d = max(round(units_30d * trend_ratio(scenario, 1)), 0)
    unit_price = 18.5 + index * 1.25

    return {
        "seller_id": SELLER_ID,
        "marketplace_id": MARKETPLACE_ID,
        "seller_sku": item["seller_sku"],
        "asin": item["asin"],
        "stat_date": TODAY,
        "sales_units_1d": units_1d,
        "sales_units_3d": units_3d,
        "sales_units_7d": units_7d,
        "sales_units_14d": units_14d,
        "sales_units_30d": units_30d,
        "avg_daily_sales_3d": round(units_3d / 3, 2),
        "avg_daily_sales_7d": round(units_7d / 7, 2),
        "avg_daily_sales_30d": round(units_30d / 30, 2),
        "sales_amount_7d": round(units_7d * unit_price, 2),
        "sales_amount_30d": round(units_30d * unit_price, 2),
        "currency": "USD",
        "sales_trend": sales_trend(scenario),
        "sales_trend_rate": sales_trend_rate(scenario),
        "data_source": "excel",
    }


def trend_ratio(scenario: str, days: int) -> float:
    daily_share = days / 30
    if scenario in {"high_stockout_risk", "stockout"}:
        return daily_share * 1.25
    if scenario == "overstock":
        return daily_share * 0.65
    return daily_share


def sales_trend(scenario: str) -> str:
    if scenario in {"high_stockout_risk", "stockout"}:
        return "up"
    if scenario == "overstock":
        return "down"
    return "stable"


def sales_trend_rate(scenario: str) -> float:
    if scenario in {"high_stockout_risk", "stockout"}:
        return 0.18
    if scenario == "overstock":
        return -0.22
    return 0.03


def config_row(item: dict) -> dict | None:
    if item["scenario"] == "data_missing" and item["scenario_index"] == 2:
        return None

    scenario = item["scenario"]
    values = {
        "normal": (7, 4, 18, 3, 7, 7, 45, 90, "ocean"),
        "high_stockout_risk": (14, 5, 28, 5, 9, 10, 50, 90, "ocean"),
        "stockout": (10, 4, 24, 4, 8, 7, 45, 80, "air"),
        "overstock": (7, 3, 16, 3, 7, 7, 35, 75, "ocean"),
        "large_inbound": (8, 4, 20, 4, 7, 7, 50, 100, "ocean"),
        "unfulfillable_issue": (7, 4, 18, 3, 7, 7, 45, 90, "ocean"),
        "data_missing": (9, 4, 20, 4, 7, 7, 45, 90, "ocean"),
    }[scenario]
    purchase, domestic, international, customs, receiving, safety, target, max_stock, method = values
    total_days = purchase + domestic + international + customs + receiving

    return {
        "seller_id": SELLER_ID,
        "marketplace_id": MARKETPLACE_ID,
        "seller_sku": item["seller_sku"],
        "supplier_name": f"Demo Supplier {item['sequence'] % 5 + 1}",
        "purchase_lead_time_days": purchase,
        "domestic_shipping_days": domestic,
        "international_shipping_days": international,
        "customs_clearance_days": customs,
        "amazon_receiving_days": receiving,
        "total_replenishment_days": total_days,
        "safety_stock_days": safety,
        "target_stock_days": target,
        "max_stock_days": max_stock,
        "moq": 50,
        "carton_quantity": 24,
        "case_pack_quantity": 12,
        "preferred_shipping_method": method,
        "reorder_point_days": total_days + safety,
        "config_status": "complete",
    }


def write_excel(path: Path, rows: list[dict], columns: list[str]) -> None:
    df = pd.DataFrame(rows, columns=columns)
    with pd.ExcelWriter(path, engine="openpyxl", date_format="YYYY-MM-DD", datetime_format="YYYY-MM-DD HH:MM:SS") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
        worksheet = writer.sheets["data"]
        worksheet.freeze_panes = "A2"
        for column_cells in worksheet.columns:
            column_name = column_cells[0].value
            max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, len(column_name) + 2), 36)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    sku_plan = build_sku_plan()
    product_rows = [product_row(item) for item in sku_plan]
    inventory_rows = [inventory_row(item) for item in sku_plan]
    sales_rows = [row for item in sku_plan if (row := sales_row(item)) is not None]
    config_rows = [row for item in sku_plan if (row := config_row(item)) is not None]

    outputs = {
        "product_master.xlsx": (product_rows, PRODUCT_MASTER_COLUMNS),
        "inventory_snapshot.xlsx": (inventory_rows, INVENTORY_SNAPSHOT_COLUMNS),
        "sales_summary.xlsx": (sales_rows, SALES_SUMMARY_COLUMNS),
        "replenishment_config.xlsx": (config_rows, REPLENISHMENT_CONFIG_COLUMNS),
    }

    for file_name, (rows, columns) in outputs.items():
        write_excel(DATA_DIR / file_name, rows, columns)

    print("Demo Excel files generated.")
    print(f"Output directory: {DATA_DIR}")
    for file_name, (rows, _) in outputs.items():
        print(f"- {file_name}: {len(rows)} rows")
    print("SKU scenario counts:")
    for _, scenario_name, count in SCENARIOS:
        print(f"- {scenario_name}: {count}")


if __name__ == "__main__":
    main()
