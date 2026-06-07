from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text

from backend.app.core.database import engine
from backend.app.schemas.task_schema import (
    TaskItem,
    TaskStatusUpdateRequest,
    TaskStatusUpdateResponse,
)


router = APIRouter(prefix="/api/tasks", tags=["tasks"])

BASE_TASK_FIELDS = [
    "task_id",
    "seller_sku",
    "asin",
    "task_type",
    "task_title",
    "task_description",
    "priority",
    "risk_level",
    "suggested_action",
    "approval_required",
    "task_status",
    "created_at",
]

EXTENDED_TASK_FIELDS = {
    "problem_type": "NULL",
    "impact_level": "NULL",
    "estimated_impact_value": "0",
    "approval_level": "NULL",
}


def _columns(table_name: str) -> set[str]:
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


def _task_fields_sql() -> str:
    task_columns = _columns("inventory_agent_tasks")
    fields = [f"t.{column}" for column in BASE_TASK_FIELDS]
    for column, default_sql in EXTENDED_TASK_FIELDS.items():
        if column in task_columns:
            fields.append(f"t.{column}")
        else:
            fields.append(f"{default_sql} AS {column}")
    return ",\n    ".join(fields)


def _build_task_filters(
    task_type: Optional[str],
    task_status: Optional[str],
    priority: Optional[str],
    seller_sku: Optional[str],
) -> tuple[str, dict[str, str]]:
    clauses: list[str] = []
    params: dict[str, str] = {}
    if task_type:
        clauses.append("t.task_type = :task_type")
        params["task_type"] = task_type
    if task_status:
        clauses.append("t.task_status = :task_status")
        params["task_status"] = task_status
    if priority:
        clauses.append("t.priority = :priority")
        params["priority"] = priority
    if seller_sku:
        clauses.append("t.seller_sku LIKE :seller_sku")
        params["seller_sku"] = f"%{seller_sku}%"

    if not clauses:
        return "", params
    return "WHERE " + " AND ".join(clauses), params


@router.get("", response_model=list[TaskItem])
def list_tasks(
    task_type: Optional[str] = Query(default=None),
    task_status: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    seller_sku: Optional[str] = Query(default=None),
) -> list[TaskItem]:
    where_sql, params = _build_task_filters(task_type, task_status, priority, seller_sku)
    query = text(
        f"""
        SELECT {_task_fields_sql()}
        FROM inventory_agent_tasks t
        {where_sql}
        ORDER BY t.created_at DESC, t.id DESC
        """
    )
    with engine.connect() as connection:
        rows = connection.execute(query, params).mappings().all()
    return [TaskItem(**dict(row)) for row in rows]


def _update_task_status(
    task_id: str,
    status: str,
    payload: Optional[TaskStatusUpdateRequest],
) -> TaskStatusUpdateResponse:
    payload = payload or TaskStatusUpdateRequest()
    query = text(
        """
        UPDATE inventory_agent_tasks
        SET task_status = :task_status,
            operator_id = :operator_id,
            operator_note = :operator_note,
            resolved_at = :resolved_at
        WHERE task_id = :task_id
        """
    )
    with engine.begin() as connection:
        result = connection.execute(
            query,
            {
                "task_status": status,
                "operator_id": payload.operator_id,
                "operator_note": payload.operator_note,
                "resolved_at": datetime.utcnow(),
                "task_id": task_id,
            },
        )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskStatusUpdateResponse(
        success=True,
        task_id=task_id,
        task_status=status,
        message=f"Task marked as {status}",
    )


@router.post("/{task_id}/resolve", response_model=TaskStatusUpdateResponse)
def resolve_task(
    task_id: str,
    payload: Optional[TaskStatusUpdateRequest] = None,
) -> TaskStatusUpdateResponse:
    return _update_task_status(task_id, "resolved", payload)


@router.post("/{task_id}/ignore", response_model=TaskStatusUpdateResponse)
def ignore_task(
    task_id: str,
    payload: Optional[TaskStatusUpdateRequest] = None,
) -> TaskStatusUpdateResponse:
    return _update_task_status(task_id, "ignored", payload)
