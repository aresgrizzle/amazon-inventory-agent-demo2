from __future__ import annotations

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from backend.app.core.config import (
    AI_ENABLED,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
    OPENAI_MODEL,
)


AI_NOT_CONFIGURED_MESSAGE = "OpenAI is not configured"
AI_REQUEST_TIMEOUT_SECONDS = 18.0
AI_MAX_TOKENS = 1000


def is_ai_configured() -> bool:
    return bool(AI_ENABLED and OPENAI_API_KEY.strip())


def generate_dashboard_summary(
    dashboard_summary: dict[str, Any],
    risk_distribution: list[dict[str, Any]],
    top_risk_skus: list[dict[str, Any]],
    open_tasks: list[dict[str, Any]],
) -> str:
    prompt = _build_dashboard_summary_prompt(
        dashboard_summary=dashboard_summary,
        risk_distribution=risk_distribution,
        top_risk_skus=top_risk_skus,
        open_tasks=open_tasks,
    )
    return _call_openai(prompt)


def generate_sku_analysis(
    sku_detail: dict[str, Any],
    sku_tasks: list[dict[str, Any]],
) -> str:
    prompt = _build_sku_analysis_prompt(sku_detail=sku_detail, sku_tasks=sku_tasks)
    return _call_openai(prompt)


def generate_task_priority(open_tasks: list[dict[str, Any]]) -> str:
    prompt = _build_task_priority_prompt(open_tasks=open_tasks)
    return _call_openai(prompt)


def _call_openai(prompt: str) -> str:
    if not is_ai_configured():
        raise RuntimeError(AI_NOT_CONFIGURED_MESSAGE)

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("OpenAI SDK is not installed") from exc

    client = OpenAI(
        api_key=OPENAI_API_KEY,
        base_url=OPENAI_BASE_URL,
        timeout=AI_REQUEST_TIMEOUT_SECONDS,
    )

    try:
        response = client.responses.create(
            model=OPENAI_MODEL,
            input=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": prompt,
                        }
                    ],
                }
            ],
            extra_body={"max_tokens": AI_MAX_TOKENS},
        )
        output_text = getattr(response, "output_text", None)
        if output_text:
            return str(output_text).strip()
        return _extract_response_text(response)
    except Exception as exc:
        if _should_fallback_to_chat_completions(exc):
            try:
                return _call_chat_completions(client, prompt)
            except Exception as chat_exc:
                raise RuntimeError(
                    f"OpenAI request failed: {chat_exc.__class__.__name__}"
                ) from chat_exc
        raise RuntimeError(f"OpenAI request failed: {exc.__class__.__name__}") from exc


def _should_fallback_to_chat_completions(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    return exc.__class__.__name__ == "NotFoundError" or status_code == 404


def _call_chat_completions(client: Any, prompt: str) -> str:
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {
                "role": "system",
                "content": "你是资深 Amazon 库存运营负责人，只用中文回答。",
            },
            {"role": "user", "content": prompt},
        ],
        extra_body={"max_tokens": AI_MAX_TOKENS},
    )
    content = response.choices[0].message.content if response.choices else None
    if not content:
        raise RuntimeError("OpenAI returned an empty response")
    return str(content).strip()


def _extract_response_text(response: Any) -> str:
    response_dict = response.model_dump() if hasattr(response, "model_dump") else {}
    output_items = response_dict.get("output", [])
    text_parts: list[str] = []
    for item in output_items:
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                text_parts.append(str(content["text"]))
    text = "\n".join(text_parts).strip()
    if not text:
        raise RuntimeError("OpenAI returned an empty response")
    return text


def _build_dashboard_summary_prompt(
    dashboard_summary: dict[str, Any],
    risk_distribution: list[dict[str, Any]],
    top_risk_skus: list[dict[str, Any]],
    open_tasks: list[dict[str, Any]],
) -> str:
    payload = {
        "dashboard_summary": dashboard_summary,
        "risk_distribution": risk_distribution,
        "top_risk_skus": top_risk_skus,
        "open_tasks": open_tasks,
    }
    return (
        "你是一名资深 Amazon 库存运营负责人。请根据系统提供的 SKU 总数、风险分布、"
        "库存异常、未完成任务数量和高风险 SKU，生成一段中文运营复盘。要求指出最高优先级问题、"
        "主要风险来源、下一步处理建议。语言要像运营负责人写给团队看的日报，不要像泛泛的 AI 助手。\n\n"
        "重要约束：不要重新计算风险，不要编造没有提供的数据，只解释系统已经计算出的结果。\n\n"
        f"系统数据：\n{_to_json(payload)}"
    )


def _build_sku_analysis_prompt(
    sku_detail: dict[str, Any],
    sku_tasks: list[dict[str, Any]],
) -> str:
    payload = {
        "sku_detail": sku_detail,
        "sku_tasks": sku_tasks,
    }
    return (
        "你是一名资深 Amazon 库存运营。请根据该 SKU 的库存、销量、风险等级、系统任务建议，"
        "解释为什么系统判断它有风险，并给出下一步处理建议。不要编造没有提供的数据。\n\n"
        "输出要求：使用中文；围绕库存、销量、断货、滞销、补货、清仓和任务处理；"
        "先给结论，再给原因和建议。\n\n"
        f"系统数据：\n{_to_json(payload)}"
    )


def _build_task_priority_prompt(open_tasks: list[dict[str, Any]]) -> str:
    payload = {
        "open_tasks": open_tasks,
    }
    return (
        "你是一名 Amazon 运营主管。请根据当前未完成任务列表，给出处理顺序建议。"
        "优先考虑断货风险，其次考虑高库存和滞销风险。请输出清晰的优先级顺序和原因。\n\n"
        "重要约束：不要重新计算风险，不要编造没有提供的数据；只基于任务列表和系统风险等级排序。\n\n"
        f"系统数据：\n{_to_json(payload)}"
    )


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=_json_default)


def _json_default(value: Any) -> str | float | int:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)
