# Amazon Inventory Agent Demo — 数据库设计

## 设计原则

1. **不使用外键约束**：表间通过业务字段 `seller_id + marketplace_id + seller_sku` 逻辑关联
2. **字段命名**：全部 snake_case
3. **表名固定**：不得擅自改名
4. **库存快照保留历史**：每次导入生成新 `sync_batch_id`，不覆盖旧记录
5. **分析可追溯**：`inventory_agent_analysis` 记录三个来源 ID
6. **任务支持状态流转**：`task_status` 字段

## 表关系总览

```
amazon_product_master
        │
        │ seller_id + marketplace_id + seller_sku
        ├──────────────────┬─────────────────────┐
        ▼                  ▼                     ▼
amazon_inventory_    amazon_sales_      inventory_replenishment_
snapshot             summary              config
        │                  │                     │
        └──────────┬───────┴─────────────────────┘
                   ▼
        inventory_agent_analysis
        (记录 snapshot_id, sales_id, config_id)
                   │
                   ▼
        inventory_agent_tasks
        (analysis_id 关联)
```

---

## 1. amazon_product_master

### 1.1 表用途

存储亚马逊商品主数据（SKU 维度），作为所有库存、销量、配置、分析数据的关联基础。

### 1.2 字段定义

| 字段名 | 类型 | 中文含义 | 字段来源 | 必填 | 默认值 |
|--------|------|---------|---------|------|--------|
| id | BIGINT UNSIGNED | 主键自增 ID | 系统生成 | 是 | AUTO_INCREMENT |
| seller_id | VARCHAR(64) | 卖家 ID | Excel / SP-API | 是 | — |
| marketplace_id | VARCHAR(32) | 站点 ID（如 ATVPDKIKX0DER） | Excel / SP-API | 是 | — |
| marketplace_name | VARCHAR(64) | 站点名称（如 Amazon.com） | Excel | 否 | NULL |
| seller_sku | VARCHAR(128) | 卖家 SKU | Excel / SP-API | 是 | — |
| asin | VARCHAR(32) | 亚马逊 ASIN | Excel / SP-API | 是 | — |
| fn_sku | VARCHAR(64) | FBA 履约 SKU | Excel / SP-API | 否 | NULL |
| product_name | VARCHAR(512) | 商品标题 | Excel / SP-API | 否 | NULL |
| brand | VARCHAR(128) | 品牌 | Excel | 否 | NULL |
| product_type | VARCHAR(64) | 商品类型 | Excel | 否 | NULL |
| category_name | VARCHAR(256) | 类目名称 | Excel | 否 | NULL |
| condition_type | VARCHAR(32) | 商品状况 | Excel / SP-API | 否 | 'New' |
| fulfillment_channel | VARCHAR(16) | 履约方式（FBA / FBM） | Excel | 否 | 'FBA' |
| listing_status | VARCHAR(32) | 刊登状态（Active / Inactive） | Excel | 否 | 'Active' |
| lifecycle_stage | VARCHAR(32) | 生命周期（launch / growth / mature / decline） | Excel / 运营维护 | 否 | NULL |
| launch_date | DATE | 上架日期 | Excel | 否 | NULL |
| is_deleted | TINYINT(1) | 是否已删除（软删除） | 系统 | 是 | 0 |
| created_at | DATETIME | 创建时间 | 系统 | 是 | CURRENT_TIMESTAMP |
| updated_at | DATETIME | 更新时间 | 系统 | 是 | CURRENT_TIMESTAMP ON UPDATE |

### 1.3 主键与索引

| 类型 | 名称 | 字段 |
|------|------|------|
| 主键 | PRIMARY | id |
| 唯一索引 | uk_seller_marketplace_sku | seller_id, marketplace_id, seller_sku |
| 普通索引 | idx_asin | asin |
| 普通索引 | idx_seller_id | seller_id |
| 普通索引 | idx_listing_status | listing_status |

### 1.4 关联关系

- 被 `amazon_inventory_snapshot`、`amazon_sales_summary`、`inventory_replenishment_config` 通过业务字段关联
- 一对多：一个 SKU 对应多条库存快照（历史批次）

---

## 2. amazon_inventory_snapshot

### 2.1 表用途

存储 FBA 库存快照，**每次同步保留新记录**，用于 Agent 分析时选取最新批次，同时支持历史追溯。

### 2.2 字段定义

| 字段名 | 类型 | 中文含义 | 字段来源 | 必填 | 默认值 |
|--------|------|---------|---------|------|--------|
| id | BIGINT UNSIGNED | 主键自增 ID | 系统生成 | 是 | AUTO_INCREMENT |
| seller_id | VARCHAR(64) | 卖家 ID | Excel / FBA Inventory API | 是 | — |
| marketplace_id | VARCHAR(32) | 站点 ID | Excel / API | 是 | — |
| seller_sku | VARCHAR(128) | 卖家 SKU | Excel / API | 是 | — |
| asin | VARCHAR(32) | ASIN | Excel / API | 是 | — |
| fn_sku | VARCHAR(64) | FBA SKU | Excel / API | 否 | NULL |
| condition_type | VARCHAR(32) | 商品状况 | Excel / API | 否 | 'New' |
| total_quantity | INT | 总库存（可售+在途+预留等） | Excel / API | 是 | 0 |
| fulfillable_quantity | INT | 可售库存 | Excel / API | 是 | 0 |
| inbound_working_quantity | INT | 在途-工作中（已创建计划） | Excel / API | 是 | 0 |
| inbound_shipped_quantity | INT | 在途-已发货 | Excel / API | 是 | 0 |
| inbound_receiving_quantity | INT | 在途-接收中 | Excel / API | 是 | 0 |
| total_reserved_quantity | INT | 预留总量 | Excel / API | 是 | 0 |
| pending_customer_order_quantity | INT | 待发货客户订单 | Excel / API | 是 | 0 |
| pending_transshipment_quantity | INT | 待转运 | Excel / API | 是 | 0 |
| fc_processing_quantity | INT | FC 处理中 | Excel / API | 是 | 0 |
| total_unfulfillable_quantity | INT | 不可售总量 | Excel / API | 是 | 0 |
| total_researching_quantity | INT | 调查中库存 | Excel / API | 是 | 0 |
| amazon_last_updated_time | DATETIME | 亚马逊侧最后更新时间 | Excel / API | 否 | NULL |
| sync_batch_id | VARCHAR(64) | 同步批次号 | 导入脚本生成 | 是 | — |
| sync_time | DATETIME | 本次同步时间 | 导入脚本生成 | 是 | — |
| created_at | DATETIME | 记录创建时间 | 系统 | 是 | CURRENT_TIMESTAMP |

### 2.3 主键与索引

| 类型 | 名称 | 字段 |
|------|------|------|
| 主键 | PRIMARY | id |
| 普通索引 | idx_sku_sync | seller_id, marketplace_id, seller_sku, sync_time |
| 普通索引 | idx_sync_batch | sync_batch_id |
| 普通索引 | idx_seller_marketplace | seller_id, marketplace_id |

> 注意：不设唯一索引，同一 SKU 可有多条历史快照。

### 2.4 关联关系

- 逻辑关联 `amazon_product_master`（seller_id + marketplace_id + seller_sku）
- 被 `inventory_agent_analysis.inventory_snapshot_id` 引用

---

## 3. amazon_sales_summary

### 3.1 表用途

存储 SKU 维度的销量汇总（多时间窗口），供 Agent 计算日均销量与可售天数。

### 3.2 字段定义

| 字段名 | 类型 | 中文含义 | 字段来源 | 必填 | 默认值 |
|--------|------|---------|---------|------|--------|
| id | BIGINT UNSIGNED | 主键自增 ID | 系统生成 | 是 | AUTO_INCREMENT |
| seller_id | VARCHAR(64) | 卖家 ID | Excel / Reports API | 是 | — |
| marketplace_id | VARCHAR(32) | 站点 ID | Excel / API | 是 | — |
| seller_sku | VARCHAR(128) | 卖家 SKU | Excel / API | 是 | — |
| asin | VARCHAR(32) | ASIN | Excel / API | 是 | — |
| stat_date | DATE | 统计截止日期 | Excel / 脚本计算 | 是 | — |
| sales_units_1d | INT | 近 1 天销量 | Excel / 计算 | 是 | 0 |
| sales_units_3d | INT | 近 3 天销量 | Excel / 计算 | 是 | 0 |
| sales_units_7d | INT | 近 7 天销量 | Excel / 计算 | 是 | 0 |
| sales_units_14d | INT | 近 14 天销量 | Excel / 计算 | 是 | 0 |
| sales_units_30d | INT | 近 30 天销量 | Excel / 计算 | 是 | 0 |
| avg_daily_sales_3d | DECIMAL(10,2) | 近 3 天日均销量 | 计算：sales_units_3d / 3 | 是 | 0.00 |
| avg_daily_sales_7d | DECIMAL(10,2) | 近 7 天日均销量 | 计算：sales_units_7d / 7 | 是 | 0.00 |
| avg_daily_sales_30d | DECIMAL(10,2) | 近 30 天日均销量 | 计算：sales_units_30d / 30 | 是 | 0.00 |
| sales_amount_7d | DECIMAL(12,2) | 近 7 天销售额 | Excel | 否 | 0.00 |
| sales_amount_30d | DECIMAL(12,2) | 近 30 天销售额 | Excel | 否 | 0.00 |
| currency | VARCHAR(8) | 币种 | Excel | 否 | 'USD' |
| sales_trend | VARCHAR(16) | 销量趋势（up / down / stable） | 计算 / Excel | 否 | NULL |
| sales_trend_rate | DECIMAL(8,4) | 趋势变化率 | 计算 | 否 | NULL |
| data_source | VARCHAR(32) | 数据来源（excel / sp_api） | 系统 | 是 | 'excel' |
| created_at | DATETIME | 创建时间 | 系统 | 是 | CURRENT_TIMESTAMP |
| updated_at | DATETIME | 更新时间 | 系统 | 是 | CURRENT_TIMESTAMP ON UPDATE |

### 3.3 主键与索引

| 类型 | 名称 | 字段 |
|------|------|------|
| 主键 | PRIMARY | id |
| 唯一索引 | uk_sku_stat_date | seller_id, marketplace_id, seller_sku, stat_date |
| 普通索引 | idx_seller_marketplace | seller_id, marketplace_id |
| 普通索引 | idx_stat_date | stat_date |

### 3.4 关联关系

- 逻辑关联 `amazon_product_master`
- 被 `inventory_agent_analysis.sales_summary_id` 引用

---

## 4. inventory_replenishment_config

### 4.1 表用途

存储 SKU 维度的补货参数配置（采购周期、安全库存天数、目标库存天数等），是 Agent 判断断货风险和补货量的关键输入。

### 4.2 字段定义

| 字段名 | 类型 | 中文含义 | 字段来源 | 必填 | 默认值 |
|--------|------|---------|---------|------|--------|
| id | BIGINT UNSIGNED | 主键自增 ID | 系统生成 | 是 | AUTO_INCREMENT |
| seller_id | VARCHAR(64) | 卖家 ID | Excel / 运营维护 | 是 | — |
| marketplace_id | VARCHAR(32) | 站点 ID | Excel | 是 | — |
| seller_sku | VARCHAR(128) | 卖家 SKU | Excel | 是 | — |
| supplier_name | VARCHAR(128) | 供应商名称 | Excel | 否 | NULL |
| purchase_lead_time_days | INT | 采购交期（天） | Excel | 是 | 0 |
| domestic_shipping_days | INT | 国内物流天数 | Excel | 是 | 0 |
| international_shipping_days | INT | 国际物流天数 | Excel | 是 | 0 |
| customs_clearance_days | INT | 清关天数 | Excel | 是 | 0 |
| amazon_receiving_days | INT | 亚马逊入仓天数 | Excel | 是 | 0 |
| total_replenishment_days | INT | 总补货周期（天） | 计算或 Excel | 是 | 0 |
| safety_stock_days | INT | 安全库存天数 | Excel | 是 | 7 |
| target_stock_days | INT | 目标库存天数 | Excel | 是 | 45 |
| max_stock_days | INT | 最大库存天数 | Excel | 是 | 90 |
| moq | INT | 最小起订量 | Excel | 否 | 1 |
| carton_quantity | INT | 箱规（每箱数量） | Excel | 否 | NULL |
| case_pack_quantity | INT | 装箱数 | Excel | 否 | NULL |
| preferred_shipping_method | VARCHAR(32) | 首选物流方式 | Excel | 否 | NULL |
| reorder_point_days | INT | 再订货点（天） | Excel | 否 | NULL |
| config_status | VARCHAR(16) | 配置状态（见附录枚举约定） | Excel | 是 | 'complete' |
| created_at | DATETIME | 创建时间 | 系统 | 是 | CURRENT_TIMESTAMP |
| updated_at | DATETIME | 更新时间 | 系统 | 是 | CURRENT_TIMESTAMP ON UPDATE |

### 4.3 主键与索引

| 类型 | 名称 | 字段 |
|------|------|------|
| 主键 | PRIMARY | id |
| 唯一索引 | uk_seller_marketplace_sku_config | seller_id, marketplace_id, seller_sku |
| 普通索引 | idx_config_status | config_status |

### 4.4 关联关系

- 逻辑关联 `amazon_product_master`
- 被 `inventory_agent_analysis.replenishment_config_id` 引用

### 4.5 计算说明

`total_replenishment_days` 可由以下字段求和，也可在 Excel 中直接填写：

```
total_replenishment_days =
  purchase_lead_time_days
  + domestic_shipping_days
  + international_shipping_days
  + customs_clearance_days
  + amazon_receiving_days
```

---

## 5. inventory_agent_analysis

### 5.1 表用途

存储库存 Agent 每次分析的结果，记录分析时依据的数据来源 ID，支持批次查询与历史对比。

### 5.2 字段定义

| 字段名 | 类型 | 中文含义 | 字段来源 | 必填 | 默认值 |
|--------|------|---------|---------|------|--------|
| id | BIGINT UNSIGNED | 主键自增 ID | 系统生成 | 是 | AUTO_INCREMENT |
| analysis_batch_id | VARCHAR(64) | 分析批次号 | Agent 服务生成 | 是 | — |
| seller_id | VARCHAR(64) | 卖家 ID | 输入 | 是 | — |
| marketplace_id | VARCHAR(32) | 站点 ID | 输入 | 是 | — |
| seller_sku | VARCHAR(128) | 卖家 SKU | 输入 | 是 | — |
| asin | VARCHAR(32) | ASIN | 输入 | 是 | — |
| analysis_date | DATE | 分析日期 | 系统 | 是 | — |
| inventory_snapshot_id | BIGINT UNSIGNED | 关联库存快照 ID | 查询结果 | 否 | NULL |
| sales_summary_id | BIGINT UNSIGNED | 关联销量汇总 ID | 查询结果 | 否 | NULL |
| replenishment_config_id | BIGINT UNSIGNED | 关联补货配置 ID | 查询结果 | 否 | NULL |
| fulfillable_quantity | INT | 分析时可售库存 | 快照 | 是 | 0 |
| total_quantity | INT | 分析时总库存 | 快照 | 是 | 0 |
| effective_inbound_quantity | INT | 有效在途库存 | 规则计算 | 是 | 0 |
| avg_daily_sales_7d | DECIMAL(10,2) | 7 天日均销量 | 销量表 | 是 | 0.00 |
| avg_daily_sales_30d | DECIMAL(10,2) | 30 天日均销量 | 销量表 | 是 | 0.00 |
| available_days | DECIMAL(10,2) | 可售库存可支撑天数 | 规则计算 | 否 | NULL |
| total_cover_days | DECIMAL(10,2) | 总库存覆盖天数 | 规则计算 | 否 | NULL |
| inbound_cover_days | DECIMAL(10,2) | 在途覆盖天数 | 规则计算 | 否 | NULL |
| total_replenishment_days | INT | 总补货周期 | 配置表 | 否 | NULL |
| safety_stock_days | INT | 安全库存天数 | 配置表 | 否 | NULL |
| estimated_stockout_date | DATE | 预计断货日期 | 规则计算 | 否 | NULL |
| stockout_risk_level | VARCHAR(16) | 断货风险等级 | 规则计算 | 是 | 'low' |
| overstock_risk_level | VARCHAR(16) | 滞销风险等级 | 规则计算 | 是 | 'low' |
| replenishment_urgency | VARCHAR(16) | 补货紧急度 | 规则计算 | 否 | NULL |
| recommended_replenishment_quantity | INT | 建议补货数量 | 规则计算 | 是 | 0 |
| recommended_replenishment_date | DATE | 建议补货日期 | 规则计算 | 否 | NULL |
| recommended_action | VARCHAR(64) | 建议动作 | 规则计算 | 是 | 'keep_monitoring' |
| action_reason | TEXT | 建议原因 | 规则计算 | 否 | NULL |
| risk_reason | TEXT | 风险原因 | 规则计算 | 否 | NULL |
| need_manual_approval | TINYINT(1) | 是否需要人工审批 | 规则计算 | 是 | 0 |
| confidence_score | DECIMAL(5,2) | 置信度分数（0-100） | 规则计算 | 否 | NULL |
| data_quality_status | VARCHAR(32) | 数据质量状态 | 规则计算 | 是 | 'complete' |
| created_at | DATETIME | 创建时间 | 系统 | 是 | CURRENT_TIMESTAMP |

### 5.3 主键与索引

| 类型 | 名称 | 字段 |
|------|------|------|
| 主键 | PRIMARY | id |
| 普通索引 | idx_batch_id | analysis_batch_id |
| 普通索引 | idx_sku_date | seller_id, marketplace_id, seller_sku, analysis_date |
| 普通索引 | idx_stockout_risk | stockout_risk_level |
| 普通索引 | idx_overstock_risk | overstock_risk_level |

### 5.4 关联关系

- `inventory_snapshot_id` → `amazon_inventory_snapshot.id`（逻辑关联，无外键）
- `sales_summary_id` → `amazon_sales_summary.id`
- `replenishment_config_id` → `inventory_replenishment_config.id`
- 一对多：一条分析可生成多条 `inventory_agent_tasks`

---

## 6. inventory_agent_tasks

### 6.1 表用途

存储 Agent 分析后生成的库存运营待办任务，支持状态流转与操作记录。

### 6.2 字段定义

| 字段名 | 类型 | 中文含义 | 字段来源 | 必填 | 默认值 |
|--------|------|---------|---------|------|--------|
| id | BIGINT UNSIGNED | 主键自增 ID | 系统生成 | 是 | AUTO_INCREMENT |
| task_id | VARCHAR(64) | 任务唯一标识（UUID） | 系统生成 | 是 | — |
| analysis_id | BIGINT UNSIGNED | 关联分析记录 ID | Agent 输出 | 是 | — |
| seller_id | VARCHAR(64) | 卖家 ID | 分析记录 | 是 | — |
| marketplace_id | VARCHAR(32) | 站点 ID | 分析记录 | 是 | — |
| seller_sku | VARCHAR(128) | 卖家 SKU | 分析记录 | 是 | — |
| asin | VARCHAR(32) | ASIN | 分析记录 | 是 | — |
| task_type | VARCHAR(64) | 任务类型 | 规则映射 | 是 | — |
| task_title | VARCHAR(256) | 任务标题 | 规则生成 | 是 | — |
| task_description | TEXT | 任务描述 | 规则生成 | 否 | NULL |
| priority | VARCHAR(16) | 优先级（critical / high / medium / low） | 规则映射 | 是 | 'medium' |
| risk_level | VARCHAR(16) | 关联风险等级 | 分析记录 | 是 | — |
| suggested_action | VARCHAR(64) | 建议操作 | 分析记录 | 是 | — |
| action_parameters | JSON | 操作参数（如补货数量） | 规则生成 | 否 | NULL |
| expected_impact | TEXT | 预期影响 | 规则生成 | 否 | NULL |
| approval_required | TINYINT(1) | 是否需要审批 | 分析记录 | 是 | 0 |
| task_status | VARCHAR(32) | 任务状态 | 运营操作 | 是 | 'pending' |
| assigned_to | VARCHAR(64) | 指派给 | 运营操作 | 否 | NULL |
| operator_id | VARCHAR(64) | 操作人 ID | 运营操作 | 否 | NULL |
| operator_note | TEXT | 操作备注 | 运营操作 | 否 | NULL |
| resolved_at | DATETIME | 解决时间 | 运营操作 | 否 | NULL |
| created_at | DATETIME | 创建时间 | 系统 | 是 | CURRENT_TIMESTAMP |
| updated_at | DATETIME | 更新时间 | 系统 | 是 | CURRENT_TIMESTAMP ON UPDATE |

### 6.3 主键与索引

| 类型 | 名称 | 字段 |
|------|------|------|
| 主键 | PRIMARY | id |
| 唯一索引 | uk_task_id | task_id |
| 普通索引 | idx_analysis_id | analysis_id |
| 普通索引 | idx_task_status | task_status |
| 普通索引 | idx_priority_status | priority, task_status |
| 普通索引 | idx_sku | seller_id, marketplace_id, seller_sku |

### 6.4 任务状态流转

```
pending → in_progress → resolved
         ↘ ignored
         ↘ cancelled
```

| 状态 | 含义 |
|------|------|
| pending | 待处理（默认） |
| in_progress | 处理中 |
| resolved | 已解决 |
| ignored | 已忽略（无需处理） |
| cancelled | 已取消 |

### 6.5 任务类型枚举

| task_type | 触发条件 |
|-----------|---------|
| stockout_warning | stockout_risk_level = critical |
| replenishment_suggestion | stockout_risk_level = high 或 recommended_action = replenish_now |
| overstock_warning | overstock_risk_level = high |
| unfulfillable_inventory_alert | total_unfulfillable_quantity > 0 |
| data_missing_alert | data_quality_status ∈ {missing_inventory, missing_sales, missing_config, invalid_sales, invalid_config} |

---

## 附录 A：DDL 文件位置

完整建表 SQL 将在 Milestone 2 创建于：

```
backend/sql/01_create_tables.sql
```

**约束提醒**：后续所有代码开发不得擅自修改上述表名与字段名。

---

## 附录 B：状态与枚举约定

所有状态字段使用 **VARCHAR**，不使用 MySQL ENUM 类型。取值必须与 `docs/agent_rules.md`、API、前端保持一致。

### stockout_risk_level（断货风险）

| 值 | 含义 |
|----|------|
| low | 库存充足，持续监控 |
| medium | 可售天数处于补货周期 + 7 天预警带 |
| high | 可售天数 ≤ 总补货周期，来不及补货 |
| critical | 已断货或可售天数 ≤ 安全库存天数 |
| unknown | 无法计算（如缺销量导致 available_days 为空） |

### overstock_risk_level（滞销风险）

| 值 | 含义 |
|----|------|
| low | 库存周转正常 |
| medium | 总覆盖天数 ≥ 90 天 |
| high | 零销量有库存，或总覆盖天数 ≥ 180 天 |
| unknown | 无法计算（如缺销量且无覆盖天数） |

> 滞销风险**不使用** critical 等级（critical 仅用于断货场景）。

### recommended_action（建议动作）

| 值 | 含义 |
|----|------|
| replenish_now | 立即补货 |
| prepare_replenishment | 提前备货 |
| clearance_or_reduce_replenishment | 清仓或减产 |
| complete_missing_data | 先补全缺失数据 |
| keep_monitoring | 持续监控 |

### data_quality_status（数据质量）

| 值 | 含义 |
|----|------|
| complete | 库存、销量、补货配置均有效，可正常分析 |
| missing_inventory | 无库存快照记录 |
| missing_sales | 无销量记录，或 7d/30d 日均均为 0 |
| missing_config | 无补货配置记录 |
| invalid_sales | 有销量记录但数据异常（如 30d 销量为负、日均与 units 不一致） |
| invalid_config | 有配置记录但参数无效（如 total_replenishment_days ≤ 0、target_stock_days < safety_stock_days） |

### task_status（任务状态）

| 值 | 含义 |
|----|------|
| pending | 待处理 |
| in_progress | 处理中 |
| resolved | 已解决 |
| ignored | 已忽略 |
| cancelled | 已取消 |

### config_status（补货配置状态，`inventory_replenishment_config`）

| 值 | 含义 |
|----|------|
| complete | 配置完整且有效，Agent 分析时优先选用 |
| missing | 记录存在但关键字段为空（如 total_replenishment_days 未填） |
| invalid | 配置存在但参数不合理（同 invalid_config 判定） |
| inactive | 已停用，不参与 Agent 分析 |

> **区分说明**：`config_status` 描述**补货配置记录**是否可用；`data_quality_status` 描述**单次 Agent 分析**时数据是否足以支撑判断。二者勿混用。
