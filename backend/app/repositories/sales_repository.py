from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from backend.app.core.database import engine


def get_latest_sales_summaries() -> pd.DataFrame:
    query = text(
        """
        SELECT *
        FROM (
            SELECT
                s.*,
                ROW_NUMBER() OVER (
                    PARTITION BY seller_id, marketplace_id, seller_sku
                    ORDER BY stat_date DESC, id DESC
                ) AS row_num
            FROM amazon_sales_summary s
        ) latest
        WHERE row_num = 1
        """
    )
    with engine.connect() as connection:
        df = pd.read_sql(query, connection)
    return df.drop(columns=["row_num"], errors="ignore")
