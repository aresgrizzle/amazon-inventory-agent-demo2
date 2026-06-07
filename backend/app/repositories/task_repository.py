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
    "problem_type",
    "impact_level",
    "estimated_impact_value",
    "approval_level",
]

TASK_SELECT_COLUMNS = [
    "task_id",
    "seller_sku",
    "asin",
    "task_type",
    "task_title",
    "task_description",
    "priority",
    "risk_level",
    "suggested_action",
    "expected_impact",
    "approval_required",
    "task_status",
    "problem_type",
    "impact_level",
    "estimated_impact_value",
    "approval_level",
    "created_at",
]


def _existing_columns(table_name: str) -> set[str]:
    query = text(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = :table_name
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(query, {"table_name": table_name}).mappings().all()
    return {str(row["COLUMN_NAME"]) for row in rows}


def _available_task_columns() -> list[str]:
    existing = _existing_columns("inventory_agent_tasks")
    return [column for column in TASK_COLUMNS if column in existing]


def _task_select_sql() -> str:
    existing = _existing_columns("inventory_agent_tasks")
    return ",\n            ".join(column for column in TASK_SELECT_COLUMNS if column in existing)


def clear_tasks() -> None:
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE inventory_agent_tasks"))


def insert_task(row: dict[str, Any]) -> int:
    columns = _available_task_columns()
    values = {column: row.get(column) for column in columns}
    columns_sql = ", ".join(columns)
    params_sql = ", ".join(f":{column}" for column in columns)
    query = text(
        f"""
        INSERT INTO inventory_agent_tasks ({columns_sql})
        VALUES ({params_sql})
        """
    )
    with engine.begin() as connection:
        result = connection.execute(query, values)
        return int(result.lastrowid)


def get_open_tasks(limit: int = 30) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            {fields}
        FROM inventory_agent_tasks
        WHERE task_status = 'pending'
        ORDER BY
            CASE priority
                WHEN 'P0' THEN 1
                WHEN 'P1' THEN 2
                WHEN 'P2' THEN 3
                ELSE 4
            END,
            created_at ASC,
            id ASC
        LIMIT :limit
        """.format(fields=_task_select_sql())
    )
    with engine.connect() as connection:
        rows = connection.execute(query, {"limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def get_tasks_by_sku(seller_sku: str) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            {fields}
        FROM inventory_agent_tasks
        WHERE seller_sku = :seller_sku
        ORDER BY
            CASE task_status
                WHEN 'pending' THEN 1
                WHEN 'resolved' THEN 2
                ELSE 3
            END,
            created_at DESC,
            id DESC
        """.format(fields=_task_select_sql())
    )
    with engine.connect() as connection:
        rows = connection.execute(query, {"seller_sku": seller_sku}).mappings().all()
    return [dict(row) for row in rows]
