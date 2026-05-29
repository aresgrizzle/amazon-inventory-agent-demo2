from __future__ import annotations

import sys
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import text


BACKEND_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BACKEND_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from backend.app.core.database import engine  # noqa: E402


DATA_DIR = BACKEND_DIR / "data"

IMPORT_TARGETS = [
    ("amazon_product_master", "product_master.xlsx"),
    ("amazon_inventory_snapshot", "inventory_snapshot.xlsx"),
    ("amazon_sales_summary", "sales_summary.xlsx"),
    ("inventory_replenishment_config", "replenishment_config.xlsx"),
]

NUMERIC_COLUMNS = {
    "amazon_inventory_snapshot": [
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
    ],
    "amazon_sales_summary": [
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
        "sales_trend_rate",
    ],
    "inventory_replenishment_config": [
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
        "reorder_point_days",
    ],
    "amazon_product_master": [
        "is_deleted",
    ],
}

DATE_COLUMNS = {
    "amazon_product_master": ["launch_date"],
    "amazon_inventory_snapshot": ["amazon_last_updated_time", "sync_time"],
    "amazon_sales_summary": ["stat_date"],
    "inventory_replenishment_config": [],
}


def read_excel_file(file_name: str) -> pd.DataFrame:
    path = DATA_DIR / file_name
    if not path.exists():
        raise FileNotFoundError(f"Excel file not found: {path}")
    return pd.read_excel(path)


def clean_dataframe(table_name: str, df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    for column in DATE_COLUMNS[table_name]:
        if column in df.columns:
            df[column] = pd.to_datetime(df[column], errors="coerce")

    for column in NUMERIC_COLUMNS[table_name]:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0)

    string_columns = [
        column
        for column in df.columns
        if column not in NUMERIC_COLUMNS[table_name] and column not in DATE_COLUMNS[table_name]
    ]
    for column in string_columns:
        df[column] = df[column].where(pd.notna(df[column]), None)

    return df


def truncate_tables() -> None:
    with engine.begin() as connection:
        for table_name, _ in IMPORT_TARGETS:
            connection.execute(text(f"TRUNCATE TABLE {table_name}"))


def import_table(table_name: str, file_name: str) -> int:
    print(f"Importing {table_name}...")
    df = read_excel_file(file_name)
    df = clean_dataframe(table_name, df)
    df.to_sql(table_name, con=engine, if_exists="append", index=False, method="multi")
    row_count = len(df)
    print(f"Imported {row_count} rows")
    return row_count


def main() -> None:
    start_time = time.perf_counter()
    total_rows = 0

    print("========== START IMPORT ==========")
    print("Reading Excel...")
    truncate_tables()

    for table_name, file_name in IMPORT_TARGETS:
        total_rows += import_table(table_name, file_name)

    elapsed = time.perf_counter() - start_time
    print("========== IMPORT SUCCESS ==========")
    print(f"Total imported rows: {total_rows}")
    print(f"Import elapsed seconds: {elapsed:.2f}")
    print("Success: True")


if __name__ == "__main__":
    main()
