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


def get_open_tasks(limit: int = 30) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            task_id,
            seller_sku,
            asin,
            task_type,
            task_title,
            task_description,
            priority,
            risk_level,
            suggested_action,
            expected_impact,
            approval_required,
            task_status,
            created_at
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
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(query, {"limit": limit}).mappings().all()
    return [dict(row) for row in rows]


def get_tasks_by_sku(seller_sku: str) -> list[dict[str, Any]]:
    query = text(
        """
        SELECT
            task_id,
            seller_sku,
            asin,
            task_type,
            task_title,
            task_description,
            priority,
            risk_level,
            suggested_action,
            expected_impact,
            approval_required,
            task_status,
            created_at
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
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(query, {"seller_sku": seller_sku}).mappings().all()
    return [dict(row) for row in rows]
