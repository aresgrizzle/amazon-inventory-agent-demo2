from __future__ import annotations

import pandas as pd
from sqlalchemy import text

from backend.app.core.database import engine


def get_replenishment_configs() -> pd.DataFrame:
    query = text(
        """
        SELECT *
        FROM inventory_replenishment_config
        ORDER BY seller_sku
        """
    )
    with engine.connect() as connection:
        return pd.read_sql(query, connection)
