from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from backend.app.core.database import engine


def get_all_products() -> pd.DataFrame:
    query = text(
        """
        SELECT
            *
        FROM amazon_product_master
        WHERE is_deleted = 0
        ORDER BY seller_sku
        """
    )
    with engine.connect() as connection:
        return pd.read_sql(query, connection)
