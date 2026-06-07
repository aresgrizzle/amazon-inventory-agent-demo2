from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from backend.app.repositories.analysis_repository import (
    get_dashboard_summary_context,
    get_latest_analysis_by_sku,
    get_risk_distribution,
    get_top_risk_skus,
)
from backend.app.repositories.task_repository import get_open_tasks, get_tasks_by_sku
from backend.app.services.ai_service import (
    AI_NOT_CONFIGURED_MESSAGE,
    generate_dashboard_summary,
    generate_sku_analysis,
    generate_task_insights,
    generate_task_priority,
    build_fallback_task_insights,
    is_ai_configured,
)


router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.get("/dashboard-summary")
def get_ai_dashboard_summary() -> dict[str, object]:
    if not is_ai_configured():
        return {"configured": False, "message": AI_NOT_CONFIGURED_MESSAGE}

    try:
        summary = generate_dashboard_summary(
            dashboard_summary=get_dashboard_summary_context(),
            risk_distribution=get_risk_distribution(),
            top_risk_skus=get_top_risk_skus(limit=10),
            open_tasks=get_open_tasks(limit=20),
        )
    except RuntimeError as exc:
        return {"configured": True, "error": str(exc)}

    return {
        "configured": True,
        "summary": summary,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/sku-analysis/{seller_sku}")
def get_ai_sku_analysis(seller_sku: str) -> dict[str, object]:
    sku_detail = get_latest_analysis_by_sku(seller_sku)
    if sku_detail is None:
        raise HTTPException(status_code=404, detail="SKU analysis result not found")

    if not is_ai_configured():
        return {
            "configured": False,
            "seller_sku": seller_sku,
            "message": AI_NOT_CONFIGURED_MESSAGE,
        }

    try:
        analysis = generate_sku_analysis(
            sku_detail=sku_detail,
            sku_tasks=get_tasks_by_sku(seller_sku),
        )
    except RuntimeError as exc:
        return {"configured": True, "seller_sku": seller_sku, "error": str(exc)}

    return {
        "configured": True,
        "seller_sku": seller_sku,
        "analysis": analysis,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/task-priority")
def get_ai_task_priority() -> dict[str, object]:
    if not is_ai_configured():
        return {"configured": False, "message": AI_NOT_CONFIGURED_MESSAGE}

    try:
        suggestion = generate_task_priority(open_tasks=get_open_tasks(limit=40))
    except RuntimeError as exc:
        return {"configured": True, "error": str(exc)}

    return {
        "configured": True,
        "suggestion": suggestion,
        "generated_at": datetime.utcnow().isoformat(),
    }


@router.get("/task-insights")
def get_ai_task_insights() -> dict[str, object]:
    open_tasks = get_open_tasks(limit=50)
    top_risk_skus = get_top_risk_skus(limit=20)

    if not is_ai_configured():
        return {
            "configured": False,
            "message": "AI service is not configured",
            "insights": build_fallback_task_insights(
                open_tasks=open_tasks,
                top_risk_skus=top_risk_skus,
            ),
        }

    try:
        insights = generate_task_insights(
            open_tasks=open_tasks,
            top_risk_skus=top_risk_skus,
            risk_distribution=get_risk_distribution(),
        )
    except RuntimeError as exc:
        return {
            "configured": True,
            "insights": build_fallback_task_insights(
                open_tasks=open_tasks,
                top_risk_skus=top_risk_skus,
            ),
            "warning": str(exc),
            "generated_at": datetime.utcnow().isoformat(),
        }

    return {
        "configured": True,
        "generated_at": datetime.utcnow().isoformat(),
        "insights": insights,
    }
