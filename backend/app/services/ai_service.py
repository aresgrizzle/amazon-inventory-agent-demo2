from __future__ import annotations

import json
import re
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
AI_MAX_TOKENS = 1800


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


def generate_task_insights(
    open_tasks: list[dict[str, Any]],
    top_risk_skus: list[dict[str, Any]],
    risk_distribution: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    prompt = _build_task_insights_prompt(
        open_tasks=open_tasks,
        top_risk_skus=top_risk_skus,
        risk_distribution=risk_distribution,
    )
    raw_text = _call_openai(prompt)
    return _parse_task_insights(raw_text)


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


def _build_task_insights_prompt(
    open_tasks: list[dict[str, Any]],
    top_risk_skus: list[dict[str, Any]],
    risk_distribution: list[dict[str, Any]],
) -> str:
    payload = {
        "open_tasks": open_tasks,
        "top_risk_skus": top_risk_skus,
        "risk_distribution": risk_distribution,
    }
    return (
        "你是一名资深 Amazon 库存运营负责人。请基于系统提供的未完成任务列表、"
        "高风险 SKU 和风险分布，归纳出 3 到 6 个结构化风险问题卡片。\n\n"
        "重要约束：\n"
        "1. 不要重新计算风险，只解释系统已经给出的 task_type、priority、risk_level、suggested_action 和 SKU 风险字段。\n"
        "2. 不要编造没有提供的 SKU、任务 ID 或库存数据。\n"
        "3. 输出必须是严格 JSON，不要输出 Markdown，不要使用代码块。\n"
        "4. related_skus 只能来自输入数据中的 seller_sku。\n"
        "5. related_task_ids 只能来自输入数据中的 task_id。\n\n"
        "JSON 格式必须为：\n"
        "{\n"
        '  "insights": [\n'
        "    {\n"
        '      "id": "critical_stockout",\n'
        '      "title": "Critical stockout risk",\n'
        '      "risk_level": "critical",\n'
        '      "priority": "P0",\n'
        '      "affected_sku_count": 9,\n'
        '      "task_count": 18,\n'
        '      "summary": "9 个 SKU 存在 critical 断货风险，需要优先处理。",\n'
        '      "recommended_action": "replenish_now",\n'
        '      "risk_points": ["部分 SKU 已经断货"],\n'
        '      "solution": ["优先确认供应商交期"],\n'
        '      "related_skus": ["DEMO-STOCKOUT-01"],\n'
        '      "related_task_ids": ["task-id"]\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        f"系统数据：\n{_to_json(payload)}"
    )


def _parse_task_insights(raw_text: str) -> list[dict[str, Any]]:
    data = _parse_json_object(raw_text)
    insights = data.get("insights")
    if not isinstance(insights, list):
        raise ValueError("AI response does not contain an insights list")
    return [_normalize_insight(insight, index) for index, insight in enumerate(insights)]


def _parse_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("AI response is not valid JSON") from None
        data = json.loads(match.group(0))
    if not isinstance(data, dict):
        raise ValueError("AI response JSON root must be an object")
    return data


def _normalize_insight(insight: Any, index: int) -> dict[str, Any]:
    if not isinstance(insight, dict):
        raise ValueError("Each insight must be an object")
    title = str(insight.get("title") or f"Risk insight {index + 1}")
    insight_id = str(
        insight.get("id")
        or re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
        or f"risk_insight_{index + 1}"
    )
    return {
        "id": insight_id,
        "title": title,
        "risk_level": str(insight.get("risk_level") or "unknown"),
        "priority": str(insight.get("priority") or "P3"),
        "affected_sku_count": _to_int(insight.get("affected_sku_count")),
        "task_count": _to_int(insight.get("task_count")),
        "summary": str(insight.get("summary") or ""),
        "recommended_action": str(insight.get("recommended_action") or "keep_monitoring"),
        "risk_points": _to_string_list(insight.get("risk_points")),
        "solution": _to_string_list(insight.get("solution")),
        "related_skus": _to_string_list(insight.get("related_skus")),
        "related_task_ids": _to_string_list(insight.get("related_task_ids")),
    }


def _to_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _to_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if item is not None and str(item).strip()]


def _to_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, default=_json_default)


def _json_default(value: Any) -> str | float | int:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return str(value)
