# Amazon Inventory Agent Demo — Agent 规则设计（第一版）

## 概述

库存 Agent 第一版采用**纯规则引擎**，不接入 LLM。所有规则实现为无副作用纯函数，位于 `backend/app/utils/agent_rules.py`，便于单元测试与后续替换。

### 规则执行顺序

```
1. 数据质量检查
2. 有效在途库存计算
3. 可售天数 / 总覆盖天数 / 在途覆盖天数
4. 预计断货日期
5. 断货风险等级
6. 滞销风险等级
7. 建议补货数量
8. 建议动作
9. 置信度评分
10. 任务生成判断（由 task_service 调用）
```

---

## 1. 可售天数计算规则

### 公式

```
IF avg_daily_sales_7d > 0:
    available_days = fulfillable_quantity / avg_daily_sales_7d
ELSE IF avg_daily_sales_30d > 0:
    available_days = fulfillable_quantity / avg_daily_sales_30d
ELSE:
    available_days = NULL
    # 后续数据质量规则会标记为 missing_sales；断货/滞销风险可置为 unknown
```

### 输入字段

| 字段 | 来源表 |
|------|--------|
| fulfillable_quantity | amazon_inventory_snapshot |
| avg_daily_sales_7d | amazon_sales_summary |
| avg_daily_sales_30d | amazon_sales_summary |

### 输出字段

| 字段 | 类型 |
|------|------|
| available_days | DECIMAL(10,2) 或 NULL |

### 示例

| fulfillable_quantity | avg_daily_sales_7d | avg_daily_sales_30d | available_days |
|---------------------|-------------------|---------------------|----------------|
| 140 | 20.00 | 15.00 | 7.00 |
| 50 | 0.00 | 10.00 | 5.00 |
| 100 | 0.00 | 0.00 | NULL |

---

## 2. 总库存覆盖天数计算规则

### 公式

```
IF avg_daily_sales_30d > 0:
    total_cover_days = total_quantity / avg_daily_sales_30d
ELSE:
    total_cover_days = NULL
```

### 输入字段

| 字段 | 来源表 |
|------|--------|
| total_quantity | amazon_inventory_snapshot |
| avg_daily_sales_30d | amazon_sales_summary |

### 输出字段

| 字段 | 类型 |
|------|------|
| total_cover_days | DECIMAL(10,2) 或 NULL |

### 示例

| total_quantity | avg_daily_sales_30d | total_cover_days |
|---------------|---------------------|------------------|
| 900 | 10.00 | 90.00 |
| 200 | 0.00 | NULL |

---

## 3. 有效在途库存计算规则

### 公式

```
effective_inbound_quantity =
    inbound_shipped_quantity + inbound_receiving_quantity
```

> **第一版说明**：`inbound_working_quantity`（已创建入库计划、货未发出）**不计入**有效在途。

### 输入字段

| 字段 | 来源表 |
|------|--------|
| inbound_shipped_quantity | amazon_inventory_snapshot |
| inbound_receiving_quantity | amazon_inventory_snapshot |

### 输出字段

| 字段 | 类型 |
|------|------|
| effective_inbound_quantity | INT |

### 示例

| inbound_working | inbound_shipped | inbound_receiving | effective_inbound |
|----------------|-----------------|-------------------|-------------------|
| 100 | 50 | 30 | 80 |
| 200 | 0 | 0 | 0 |

### 在途覆盖天数（辅助字段）

```
IF avg_daily_sales_30d > 0:
    inbound_cover_days = effective_inbound_quantity / avg_daily_sales_30d
ELSE:
    inbound_cover_days = NULL
```

---

## 4. 预计断货日期

### 公式

```
IF available_days IS NOT NULL:
    estimated_stockout_date = analysis_date + timedelta(days=floor(available_days))
ELSE:
    estimated_stockout_date = NULL
```

### 输入字段

| 字段 | 说明 |
|------|------|
| available_days | 规则 1 输出 |
| analysis_date | 分析当日（通常为 today） |

### 输出字段

| 字段 | 类型 |
|------|------|
| estimated_stockout_date | DATE 或 NULL |

### 示例

| analysis_date | available_days | estimated_stockout_date |
|--------------|----------------|------------------------|
| 2025-05-25 | 7.00 | 2025-06-01 |
| 2025-05-25 | NULL | NULL |

---

## 5. 断货风险等级（stockout_risk_level）

### 规则（按优先级从上到下匹配，命中即返回）

| 优先级 | 条件 | 结果 |
|--------|------|------|
| 1 | fulfillable_quantity = 0 | **critical** |
| 2 | available_days IS NOT NULL AND available_days <= safety_stock_days | **critical** |
| 3 | available_days IS NOT NULL AND available_days <= total_replenishment_days | **high** |
| 4 | available_days IS NOT NULL AND available_days <= total_replenishment_days + 7 | **medium** |
| 5 | 其他 | **low** |

### 输入字段

| 字段 | 来源 |
|------|------|
| fulfillable_quantity | 库存快照 |
| available_days | 规则 1 |
| safety_stock_days | 补货配置 |
| total_replenishment_days | 补货配置 |

### 输出字段

| 字段 | 枚举值 |
|------|--------|
| stockout_risk_level | critical / high / medium / low / unknown |

### 示例

| fulfillable | available_days | safety_stock_days | total_replenishment_days | 结果 |
|------------|----------------|--------------------|-----------------------|------|
| 0 | — | 7 | 30 | critical |
| 50 | 5.0 | 7 | 30 | critical |
| 200 | 25.0 | 7 | 30 | high |
| 300 | 35.0 | 7 | 30 | medium |
| 500 | 60.0 | 7 | 30 | low |

### risk_reason 生成模板

```
critical: "可售库存为0，已断货" 或 "可售天数({available_days}) <= 安全库存天数({safety_stock_days})"
high:     "可售天数({available_days}) <= 补货周期({total_replenishment_days})，来不及补货"
medium:   "可售天数({available_days}) <= 补货周期+7天({total_replenishment_days + 7})"
low:      "库存充足，持续监控"
```

---

## 6. 滞销风险等级（overstock_risk_level）

### 规则（按优先级从上到下匹配）

| 优先级 | 条件 | 结果 |
|--------|------|------|
| 1 | avg_daily_sales_30d = 0 AND total_quantity > 0 | **high** |
| 2 | total_cover_days IS NOT NULL AND total_cover_days >= 180 | **high** |
| 3 | total_cover_days IS NOT NULL AND total_cover_days >= 90 | **medium** |
| 4 | 其他（含无法计算覆盖天数） | **low** 或 **unknown** |

### 输入字段

| 字段 | 来源 |
|------|------|
| avg_daily_sales_30d | 销量表 |
| total_quantity | 库存快照 |
| total_cover_days | 规则 2 |

### 输出字段

| 字段 | 枚举值 |
|------|--------|
| overstock_risk_level | high / medium / low / unknown |

### 示例

| avg_daily_sales_30d | total_quantity | total_cover_days | 结果 |
|--------------------|-----------------|-----------------|------|
| 0.00 | 500 | NULL | high |
| 5.00 | 1000 | 200.00 | high |
| 5.00 | 500 | 100.00 | medium |
| 10.00 | 300 | 30.00 | low |

---

## 7. 建议补货数量（recommended_replenishment_quantity）

### 公式

```
raw_qty = (target_stock_days × avg_daily_sales_30d)
          - fulfillable_quantity
          - effective_inbound_quantity

recommended_replenishment_quantity = max(0, raw_qty)

IF carton_quantity IS NOT NULL AND carton_quantity > 0:
    recommended_replenishment_quantity = ceil(recommended_replenishment_quantity / carton_quantity) × carton_quantity

IF recommended_replenishment_quantity < moq:
    recommended_replenishment_quantity = moq  # 当 moq > 0 时
```

### 输入字段

| 字段 | 来源 |
|------|------|
| target_stock_days | 补货配置 |
| avg_daily_sales_30d | 销量表 |
| fulfillable_quantity | 库存快照 |
| effective_inbound_quantity | 规则 3 |
| carton_quantity | 补货配置 |
| moq | 补货配置 |

### 输出字段

| 字段 | 类型 |
|------|------|
| recommended_replenishment_quantity | INT |

### 示例

| target_stock_days | avg_daily_sales_30d | fulfillable | effective_inbound | carton | 结果 |
|------------------|---------------------|------------|-------------------|--------|------|
| 45 | 10 | 100 | 50 | 24 | 270 → ceil(270/24)*24 = 288 |
| 45 | 10 | 500 | 0 | NULL | 0（已充足） |
| 45 | 10 | 100 | 0 | NULL | 350 |

计算过程：45×10 - 100 - 0 = 350

---

## 8. 建议动作（recommended_action）

### 规则（按优先级从上到下匹配）

| 优先级 | 条件 | recommended_action |
|--------|------|-------------------|
| 1 | data_quality_status ≠ complete | **complete_missing_data** |
| 2 | stockout_risk ∈ {critical, high} AND recommended_replenishment_quantity > 0 | **replenish_now** |
| 3 | stockout_risk = medium | **prepare_replenishment** |
| 4 | overstock_risk = high | **clearance_or_reduce_replenishment** |
| 5 | 其他 | **keep_monitoring** |

### action_reason 模板

| action | reason 示例 |
|--------|--------------|
| replenish_now | "断货风险{stockout_risk_level}，建议立即补货{recommended_replenishment_quantity}件" |
| prepare_replenishment | "断货风险medium，建议提前备货到仓" |
| clearance_or_reduce_replenishment | "滞销风险high，总覆盖{total_cover_days}天，建议清仓或减产" |
| complete_missing_data | "缺少{缺失类型}数据，请先补全" |
| keep_monitoring | "风险可控，持续监控" |

### 补货紧急度（replenishment_urgency）

| stockout_risk | urgency |
|--------------|---------|
| critical | urgent |
| high | high |
| medium | normal |
| low | none |

### need_manual_approval

第一版仅使用 `inventory_agent_analysis` 已有字段判断，**不引入**成本、广告、利润相关字段：

```
need_manual_approval = 1 IF (
    stockout_risk_level = 'critical'
    OR recommended_action IN ('replenish_now', 'clearance_or_reduce_replenishment')
    OR recommended_replenishment_quantity >= 500
) ELSE 0
```

---

## 9. 任务生成规则

由 `task_service.generate_tasks()` 在分析完成后执行。

### 9.1 需要生成任务的条件

| 序号 | 条件 | task_type | priority |
|------|------|-----------|----------|
| 1 | stockout_risk_level = critical | stockout_warning | critical |
| 2 | stockout_risk_level = high | replenishment_suggestion | high |
| 3 | overstock_risk_level = high | overstock_warning | high |
| 4 | total_unfulfillable_quantity > 0（见下方说明） | unfulfillable_inventory_alert | medium |
| 5 | data_quality_status = missing_sales | data_missing_alert | medium |
| 6 | data_quality_status = missing_config | data_missing_alert | medium |
| 7 | data_quality_status = missing_inventory | data_missing_alert | high |
| 8 | data_quality_status = invalid_sales | data_missing_alert | medium |
| 9 | data_quality_status = invalid_config | data_missing_alert | medium |

> **字段来源说明**：`total_unfulfillable_quantity` 来自 `amazon_inventory_snapshot`（通过 `inventory_snapshot_id` 关联），**不是** `inventory_agent_analysis` 表字段。任务生成服务需从快照读取该值。

> 同一 SKU 同一批次可生成多条任务（如同时断货 + 不可售）。

### 9.2 任务字段生成

```python
task_id = str(uuid.uuid4())
task_title = TASK_TITLE_MAP[task_type].format(seller_sku=seller_sku)
task_description = 根据 analysis 字段拼接
action_parameters = {
    "recommended_replenishment_quantity": recommended_replenishment_quantity,
    "recommended_action": recommended_action,
    "estimated_stockout_date": str(estimated_stockout_date),
}
suggested_action = recommended_action
approval_required = need_manual_approval
task_status = "pending"
```

### 9.3 任务标题模板

| task_type | task_title 模板 |
|-----------|----------------|
| stockout_warning | 【断货预警】{seller_sku} 可售库存已耗尽或即将断货 |
| replenishment_suggestion | 【补货建议】{seller_sku} 建议补货 {recommended_replenishment_quantity} 件 |
| overstock_warning | 【滞销预警】{seller_sku} 库存积压，覆盖 {total_cover_days} 天 |
| unfulfillable_inventory_alert | 【不可售库存】{seller_sku} 存在 {total_unfulfillable_quantity} 件不可售 |
| data_missing_alert | 【数据缺失】{seller_sku} 缺少{缺失类型}，无法准确分析 |

### 示例

**输入分析结果（`inventory_agent_analysis`）+ 关联快照字段：**

```json
{
  "seller_sku": "SKU-001",
  "inventory_snapshot_id": 101,
  "stockout_risk_level": "critical",
  "overstock_risk_level": "low",
  "recommended_replenishment_quantity": 288,
  "recommended_action": "replenish_now",
  "data_quality_status": "complete"
}
```

关联 `amazon_inventory_snapshot.id = 101` 读取：`total_unfulfillable_quantity = 5`

**输出任务（2 条）：**

1. `stockout_warning`, priority=critical
2. `unfulfillable_inventory_alert`, priority=medium

---

## 10. 数据质量规则（data_quality_status）

### 判断逻辑（按优先级从上到下匹配）

```
IF 无库存快照记录:
    status = "missing_inventory"
ELSE IF 无销量记录 OR (avg_daily_sales_7d = 0 AND avg_daily_sales_30d = 0):
    status = "missing_sales"
ELSE IF 无补货配置记录:
    status = "missing_config"
ELSE IF 销量数据异常（如 sales_units_30d < 0，或 avg_daily_sales_30d 与 units 不一致）:
    status = "invalid_sales"
ELSE IF 补货配置无效（config_status IN ('missing','invalid') 或 total_replenishment_days <= 0）:
    status = "invalid_config"
ELSE IF config_status = 'inactive':
    status = "missing_config"
ELSE:
    status = "complete"
```

### 枚举值

与 `docs/database_design.md` 附录 B 一致：

| 值 | 含义 |
|----|------|
| complete | 数据完整，可正常分析 |
| missing_inventory | 缺少库存数据 |
| missing_sales | 缺少销量或零销量 |
| missing_config | 缺少补货配置或配置已停用 |
| invalid_sales | 销量数据异常 |
| invalid_config | 补货配置参数无效 |

### 置信度评分（confidence_score）

| 条件 | 分数 |
|------|------|
| complete + 有 7d 和 30d 销量 | 90–100 |
| complete + 仅 30d 销量 | 70–89 |
| missing_sales（有库存） | 40–69 |
| missing_config | 30–49 |
| missing_inventory | 0–29 |

```python
# 简化实现
if data_quality_status == "complete":
    if avg_daily_sales_7d > 0:
        confidence_score = 95.0
    else:
        confidence_score = 75.0
elif data_quality_status == "missing_sales":
    confidence_score = 50.0
elif data_quality_status == "missing_config":
    confidence_score = 40.0
elif data_quality_status in ("invalid_sales", "invalid_config"):
    confidence_score = 35.0
else:
    confidence_score = 20.0
```

### 风险等级与 unknown

当 `available_days` 或 `total_cover_days` 无法计算时：

- `stockout_risk_level` 可置为 `unknown`（除非 `fulfillable_quantity = 0`，仍为 `critical`）
- `overstock_risk_level` 在无法计算覆盖天数且不满足零销量积压条件时，可置为 `unknown`

---

## 附录：AgentInput / AgentOutput 数据结构

### AgentInput（Python dataclass 或 Pydantic Model）

```python
class AgentInput(BaseModel):
    seller_id: str
    marketplace_id: str
    seller_sku: str
    asin: str
    analysis_date: date
    # 库存
    fulfillable_quantity: int
    total_quantity: int
    inbound_shipped_quantity: int
    inbound_receiving_quantity: int
    inbound_working_quantity: int
    total_unfulfillable_quantity: int
    # 销量
    avg_daily_sales_7d: Decimal
    avg_daily_sales_30d: Decimal
    # 配置
    safety_stock_days: int
    target_stock_days: int
    total_replenishment_days: int
    carton_quantity: Optional[int]
    moq: int
    config_status: str
    # 来源 ID
    inventory_snapshot_id: Optional[int]
    sales_summary_id: Optional[int]
    replenishment_config_id: Optional[int]
```

### AgentOutput

```python
class AgentOutput(BaseModel):
    available_days: Optional[Decimal]
    total_cover_days: Optional[Decimal]
    inbound_cover_days: Optional[Decimal]
    effective_inbound_quantity: int
    estimated_stockout_date: Optional[date]
    stockout_risk_level: str
    overstock_risk_level: str
    replenishment_urgency: Optional[str]
    recommended_replenishment_quantity: int
    recommended_replenishment_date: Optional[date]
    recommended_action: str
    action_reason: str
    risk_reason: str
    need_manual_approval: bool
    confidence_score: Decimal
    data_quality_status: str
```

---

## 附录：规则单元测试用例清单

| 用例 ID | 场景 | 期望 |
|---------|------|------|
| R01 | 正常 SKU，库存充足 | stockout=low, action=keep_monitoring |
| R02 | fulfillable=0 | stockout=critical, action=replenish_now |
| R03 | available_days < safety_stock_days | stockout=critical |
| R04 | 零销量 + 有库存 | overstock=high, available_days=NULL |
| R05 | total_cover_days=200 | overstock=high |
| R06 | 补货量含箱规取整 | qty 为 carton 整数倍 |
| R07 | 缺销量数据 | data_quality=missing_sales |
| R08 | 同时 critical + unfulfillable | 生成 2 条任务 |
