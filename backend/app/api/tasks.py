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

TASK_FIELDS = """
    task_id,
    seller_sku,
    asin,
    task_type,
    task_title,
    task_description,
    priority,
    risk_level,
    suggested_action,
    approval_required,
    task_status,
    created_at
"""


def _build_task_filters(
    task_type: Optional[str],
    task_status: Optional[str],
    priority: Optional[str],
    seller_sku: Optional[str],
) -> tuple[str, dict[str, str]]:
    clauses: list[str] = []
    params: dict[str, str] = {}
    if task_type:
        clauses.append("task_type = :task_type")
        params["task_type"] = task_type
    if task_status:
        clauses.append("task_status = :task_status")
        params["task_status"] = task_status
    if priority:
        clauses.append("priority = :priority")
        params["priority"] = priority
    if seller_sku:
        clauses.append("seller_sku LIKE :seller_sku")
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
        SELECT {TASK_FIELDS}
        FROM inventory_agent_tasks
        {where_sql}
        ORDER BY created_at DESC, id DESC
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
