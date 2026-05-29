from __future__ import annotations

from typing import Any

from sqlalchemy import text

from backend.app.core.database import engine


TASK_COLUMNS = [
    "task_id",
    "analysis_id",
    "seller_id",
    "marketplace_id",
    "seller_sku",
    "asin",
    "task_type",
    "task_title",
    "task_description",
    "priority",
    "risk_level",
    "suggested_action",
    "action_parameters",
    "expected_impact",
    "approval_required",
    "task_status",
    "assigned_to",
    "operator_id",
    "operator_note",
    "resolved_at",
]


def clear_tasks() -> None:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE inventory_agent_tasks"))


def insert_task(row: dict[str, Any]) -> int:
    values = {column: row.get(column) for column in TASK_COLUMNS}
    columns_sql = ", ".join(TASK_COLUMNS)
    params_sql = ", ".join(f":{column}" for column in TASK_COLUMNS)
    query = text(
        f"""
        INSERT INTO inventory_agent_tasks ({columns_sql})
        VALUES ({params_sql})
        """
    )
    with engine.begin() as connection:
        result = connection.execute(query, values)
        return int(result.lastrowid)
