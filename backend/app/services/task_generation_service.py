from __future__ import annotations

import json
from typing import Any
from uuid import uuid4

from backend.app.repositories.task_repository import insert_task


PRIORITY_MAP = {
    "critical": "P0",
    "high": "P1",
    "medium": "P2",
    "low": "P3",
    "unknown": "P2",
}


def _priority(risk_level: str) -> str:
    return PRIORITY_MAP.get(risk_level, "P2")


def _impact_level(value: float) -> str:
    if value >= 5000:
        return "high"
    if value >= 1000:
        return "medium"
    if value > 0:
        return "low"
    return "none"


def _priority_with_impact(risk_level: str, impact_value: float) -> str:
    if risk_level == "critical":
        return "P0"
    if risk_level == "high" and impact_value >= 3000:
        return "P0"
    if impact_value >= 5000:
        return "P1"
    return _priority(risk_level)


def _approval_level(analysis: dict[str, Any], impact_value: float) -> str:
    if not analysis.get("need_manual_approval"):
        return "none"
    if impact_value >= 5000:
        return "manager"
    return "operator"


def _estimated_overstock_value(analysis: dict[str, Any]) -> float:
    landed_cost = float(analysis.get("landed_cost") or 0)
    if landed_cost <= 0:
        landed_cost = 10.0
    return round(float(analysis.get("total_quantity") or 0) * landed_cost, 2)


def _base_task(
    analysis: dict[str, Any],
    task_type: str,
    task_title: str,
    task_description: str,
    risk_level: str,
    problem_type: str,
    estimated_impact_value: float = 0.0,
) -> dict[str, Any]:
    action_payload = {
        "seller_sku": analysis["seller_sku"],
        "recommended_quantity": analysis["recommended_replenishment_quantity"],
        "recommended_action": analysis["recommended_action"],
        "estimated_impact_value": round(float(estimated_impact_value or 0), 2),
        "estimated_lost_revenue": analysis.get("estimated_lost_revenue", 0),
        "decision_confidence": analysis.get("decision_confidence"),
        "approval_required": bool(analysis.get("need_manual_approval")),
        "estimated_stockout_date": str(analysis["estimated_stockout_date"])
        if analysis.get("estimated_stockout_date") is not None
        else None,
    }

    impact_value = float(estimated_impact_value or 0)
    return {
        "task_id": str(uuid4()),
        "analysis_id": analysis["id"],
        "seller_id": analysis["seller_id"],
        "marketplace_id": analysis["marketplace_id"],
        "seller_sku": analysis["seller_sku"],
        "asin": analysis["asin"],
        "task_type": task_type,
        "task_title": task_title,
        "task_description": task_description,
        "priority": _priority_with_impact(risk_level, impact_value),
        "risk_level": risk_level,
        "suggested_action": analysis["recommended_action"],
        "action_parameters": json.dumps(action_payload, ensure_ascii=False),
        "expected_impact": analysis.get("risk_reason") or analysis.get("action_reason"),
        "approval_required": analysis["need_manual_approval"],
        "task_status": "pending",
        "assigned_to": None,
        "operator_id": None,
        "operator_note": None,
        "resolved_at": None,
        "problem_type": problem_type,
        "impact_level": _impact_level(impact_value),
        "estimated_impact_value": round(impact_value, 2),
        "approval_level": _approval_level(analysis, impact_value),
    }


def _tasks_for_analysis(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    seller_sku = analysis["seller_sku"]
    stockout_risk = analysis["stockout_risk_level"]
    overstock_risk = analysis["overstock_risk_level"]
    recommended_quantity = analysis["recommended_replenishment_quantity"]
    estimated_lost_revenue = float(analysis.get("estimated_lost_revenue") or 0)

    if stockout_risk in {"critical", "high"}:
        tasks.append(
            _base_task(
                analysis=analysis,
                task_type="stockout_warning",
                task_title=f"[Stockout warning] {seller_sku} has {stockout_risk} stockout risk",
                task_description=analysis["action_reason"],
                risk_level=stockout_risk,
                problem_type="stockout",
                estimated_impact_value=estimated_lost_revenue,
            )
        )

    if analysis["recommended_action"] in {"replenish_now", "prepare_replenishment"}:
        risk_level = stockout_risk if stockout_risk in PRIORITY_MAP else "medium"
        tasks.append(
            _base_task(
                analysis=analysis,
                task_type="replenishment_suggestion",
                task_title=f"[Replenishment suggestion] {seller_sku} replenish {recommended_quantity} units",
                task_description=analysis["action_reason"],
                risk_level=risk_level,
                problem_type="replenishment",
                estimated_impact_value=estimated_lost_revenue,
            )
        )

    if overstock_risk == "high":
        tasks.append(
            _base_task(
                analysis=analysis,
                task_type="overstock_warning",
                task_title=f"[Overstock warning] {seller_sku} has excessive inventory cover",
                task_description=analysis["action_reason"],
                risk_level="high",
                problem_type="overstock",
                estimated_impact_value=_estimated_overstock_value(analysis),
            )
        )

    if analysis.get("total_unfulfillable_quantity", 0) > 0:
        tasks.append(
            _base_task(
                analysis=analysis,
                task_type="unfulfillable_inventory_alert",
                task_title=f"[Unfulfillable inventory] {seller_sku} has unfulfillable inventory",
                task_description=(
                    f"{seller_sku} currently has "
                    f"{analysis['total_unfulfillable_quantity']} unfulfillable units."
                ),
                risk_level="medium",
                problem_type="inventory_exception",
                estimated_impact_value=0.0,
            )
        )

    if analysis["data_quality_status"] != "complete":
        risk_level = "high" if analysis["data_quality_status"] == "missing_inventory" else "medium"
        tasks.append(
            _base_task(
                analysis=analysis,
                task_type="data_missing_alert",
                task_title=f"[Data quality] {seller_sku} data quality is {analysis['data_quality_status']}",
                task_description=(
                    f"{seller_sku} data quality is {analysis['data_quality_status']}; "
                    "complete the missing data before relying on the recommendation."
                ),
                risk_level=risk_level,
                problem_type="data_quality",
                estimated_impact_value=0.0,
            )
        )

    return tasks


def generate_tasks(analysis_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    created_tasks: list[dict[str, Any]] = []
    for analysis in analysis_results:
        for task in _tasks_for_analysis(analysis):
            task["id"] = insert_task(task)
            created_tasks.append(task)
    return created_tasks
