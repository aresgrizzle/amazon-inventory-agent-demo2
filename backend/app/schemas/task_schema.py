from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TaskItem(BaseModel):
    task_id: str
    seller_sku: str
    asin: str
    task_type: str
    task_title: str
    task_description: Optional[str]
    priority: str
    risk_level: str
    suggested_action: str
    approval_required: bool
    task_status: str
    created_at: datetime
    problem_type: Optional[str] = None
    impact_level: Optional[str] = None
    estimated_impact_value: Optional[float] = None
    approval_level: Optional[str] = None


class TaskStatusUpdateRequest(BaseModel):
    operator_id: Optional[str] = None
    operator_note: Optional[str] = None


class TaskStatusUpdateResponse(BaseModel):
    success: bool
    task_id: str
    task_status: str
    message: str
