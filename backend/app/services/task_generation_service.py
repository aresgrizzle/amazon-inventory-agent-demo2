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


def _base_task(
    analysis: dict[str, Any],
    task_type: str,
    task_title: str,
    task_description: str,
    risk_level: str,
) -> dict[str, Any]:
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
        "priority": _priority(risk_level),
        "risk_level": risk_level,
        "suggested_action": analysis["recommended_action"],
        "action_parameters": json.dumps(
            {
                "recommended_replenishment_quantity": analysis[
                    "recommended_replenishment_quantity"
                ],
                "recommended_action": analysis["recommended_action"],
                "estimated_stockout_date": str(analysis["estimated_stockout_date"])
                if analysis.get("estimated_stockout_date") is not None
                else None,
            },
            ensure_ascii=False,
        ),
        "expected_impact": analysis["action_reason"],
        "approval_required": analysis["need_manual_approval"],
        "task_status": "pending",
        "assigned_to": None,
        "operator_id": None,
        "operator_note": None,
        "resolved_at": None,
    }


def _tasks_for_analysis(analysis: dict[str, Any]) -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    seller_sku = analysis["seller_sku"]
    stockout_risk = analysis["stockout_risk_level"]
    overstock_risk = analysis["overstock_risk_level"]
    recommended_quantity = analysis["recommended_replenishment_quantity"]

    if stockout_risk in {"critical", "high"}:
        tasks.append(
            _base_task(
                analysis,
                "stockout_warning",
                f"[断货预警] {seller_sku} 存在 {stockout_risk} 断货风险",
                analysis["action_reason"],
                stockout_risk,
            )
        )

    if analysis["recommended_action"] in {"replenish_now", "prepare_replenishment"}:
        risk_level = stockout_risk if stockout_risk in PRIORITY_MAP else "medium"
        tasks.append(
            _base_task(
                analysis,
                "replenishment_suggestion",
                f"[补货建议] {seller_sku} 建议补货 {recommended_quantity} 件",
                analysis["action_reason"],
                risk_level,
            )
        )

    if overstock_risk == "high":
        tasks.append(
            _base_task(
                analysis,
                "overstock_warning",
                f"[滞销预警] {seller_sku} 库存覆盖天数过高",
                analysis["action_reason"],
                "high",
            )
        )

    if analysis.get("total_unfulfillable_quantity", 0) > 0:
        tasks.append(
            _base_task(
                analysis,
                "unfulfillable_inventory_alert",
                f"[不可售库存] {seller_sku} 存在不可售库存",
                f"{seller_sku} 当前不可售库存为 {analysis['total_unfulfillable_quantity']} 件。",
                "medium",
            )
        )

    if analysis["data_quality_status"] != "complete":
        risk_level = "high" if analysis["data_quality_status"] == "missing_inventory" else "medium"
        tasks.append(
            _base_task(
                analysis,
                "data_missing_alert",
                f"[数据缺失] {seller_sku} 数据质量状态为 {analysis['data_quality_status']}",
                f"{seller_sku} 当前数据质量状态为 {analysis['data_quality_status']}，请先补全数据。",
                risk_level,
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
