# Amazon Inventory Agent Demo — 系统架构

## 1. 整体系统架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           表现层 (Presentation)                        │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  React + Vite 前端                                               │   │
│  │  - 库存总览 Dashboard                                            │   │
│  │  - 库存分析列表                                                  │   │
│  │  - 今日待办 Tasks                                                │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │ HTTP / JSON (Axios)
┌───────────────────────────────────▼─────────────────────────────────────┐
│                           接口层 (API Layer)                             │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │  FastAPI                                                         │   │
│  │  - /api/v1/inventory/*                                           │   │
│  │  - /api/v1/agent/*                                               │   │
│  │  - /api/v1/tasks/*                                                 │   │
│  └─────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                           服务层 (Service Layer)                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │ Import       │  │ Inventory    │  │ Agent        │  │ Task       │ │
│  │ Service      │  │ Query Svc    │  │ Analysis Svc │  │ Generator  │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘ │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │  Agent Rules Engine（纯函数，无 LLM）                             │   │
│  └──────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                           数据访问层 (Repository Layer)                  │
│  SQLAlchemy ORM + PyMySQL                                                 │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                           数据层 (Data Layer)                            │
│  MySQL 8.x — 6 张核心业务表                                              │
└───────────────────────────────────┬─────────────────────────────────────┘
                                    │
┌───────────────────────────────────▼─────────────────────────────────────┐
│                           数据源 (Data Source)                           │
│  MVP: Excel (.xlsx)  →  后续: Amazon SP-API                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### 设计原则

- **分层清晰**：API 不直接操作 SQL，通过 Service → Repository
- **规则可测**：Agent 规则为纯函数，独立单元测试
- **无外键**：表间用业务字段关联（seller_id + marketplace_id + seller_sku）
- **历史可追溯**：库存快照保留多批次，分析结果记录来源 ID

---

## 2. 数据流架构

```
Excel 文件
    │
    │  pandas + openpyxl 读取
    ▼
Import Service ──────────────────────────────────────────┐
    │                                                     │
    ├──▶ amazon_product_master                            │
    ├──▶ amazon_inventory_snapshot (含 sync_batch_id)     │
    ├──▶ amazon_sales_summary                           │
    └──▶ inventory_replenishment_config                   │
                                                          │
Agent Analysis Service ◀──────────────────────────────────┘
    │
    │  读取最新 snapshot + sales + config（按 SKU 关联）
    │  调用 rules engine 计算
    ▼
inventory_agent_analysis (写入分析批次 analysis_batch_id)
    │
    │  Task Generator Service
    ▼
inventory_agent_tasks
    │
    │  FastAPI 查询
    ▼
React 前端展示
```

---

## 3. 模块划分

| 模块 | 职责 | 主要文件位置 |
|------|------|-------------|
| **core** | 配置、数据库连接、常量 | `backend/app/core/` |
| **schemas** | Pydantic 请求/响应模型 | `backend/app/schemas/` |
| **repositories** | 数据库 CRUD | `backend/app/repositories/` |
| **services** | 业务逻辑编排 | `backend/app/services/` |
| **api** | 路由与控制器 | `backend/app/api/` |
| **utils** | 规则引擎、工具函数 | `backend/app/utils/` |
| **scripts** | 导入、分析、建表脚本 | `backend/scripts/` |
| **sql** | DDL 建表语句 | `backend/sql/` |
| **data** | Excel 模板与模拟数据 | `backend/data/` |
| **frontend/api** | Axios 封装 | `frontend/src/api/` |
| **frontend/pages** | 页面组件 | `frontend/src/pages/` |
| **frontend/components** | 可复用 UI | `frontend/src/components/` |

---

## 4. 后端目录结构

```
backend/
├── app/
│   ├── main.py                 # FastAPI 入口，路由注册，CORS
│   ├── core/
│   │   ├── config.py           # 环境变量、数据库 URL
│   │   ├── database.py         # SQLAlchemy engine、SessionLocal
│   │   └── constants.py        # 风险等级、任务类型等枚举
│   ├── api/
│   │   ├── v1/
│   │   │   ├── inventory.py    # 库存查询、总览
│   │   │   ├── agent.py        # 触发分析、查询分析结果
│   │   │   └── tasks.py        # 任务 CRUD
│   │   └── deps.py             # 依赖注入：get_db
│   ├── services/
│   │   ├── import_service.py   # Excel 导入
│   │   ├── agent_service.py    # Agent 分析编排
│   │   ├── task_service.py     # 任务生成与管理
│   │   └── dashboard_service.py# 总览聚合
│   ├── repositories/
│   │   ├── product_repo.py
│   │   ├── inventory_repo.py
│   │   ├── sales_repo.py
│   │   ├── config_repo.py
│   │   ├── analysis_repo.py
│   │   └── task_repo.py
│   ├── schemas/
│   │   ├── product.py
│   │   ├── inventory.py
│   │   ├── agent.py
│   │   └── task.py
│   └── utils/
│       ├── agent_rules.py      # 规则引擎纯函数
│       └── excel_parser.py     # Excel 解析
├── scripts/
│   ├── init_db.py              # 执行建表 SQL
│   ├── import_excel.py         # Excel 导入
│   ├── run_agent_analysis.py   # 命令行触发分析
│   └── generate_mock_excel.py  # 生成模拟 Excel
├── sql/
│   └── 01_create_tables.sql    # 6 张表 DDL
├── data/
│   ├── templates/              # Excel 空模板
│   └── mock/                   # 模拟数据 xlsx
├── tests/
│   ├── test_agent_rules.py
│   └── test_import.py
├── .env.example
└── requirements.txt
```

---

## 5. 前端目录结构

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.js           # Axios 实例、baseURL
│   │   ├── inventory.js
│   │   ├── agent.js
│   │   └── tasks.js
│   ├── pages/
│   │   ├── Dashboard.jsx       # 库存总览
│   │   ├── InventoryList.jsx   # 库存分析列表
│   │   └── TodayTasks.jsx      # 今日待办
│   ├── components/
│   │   ├── Layout.jsx
│   │   ├── StatCard.jsx
│   │   ├── RiskBadge.jsx
│   │   ├── InventoryTable.jsx
│   │   └── TaskTable.jsx
│   ├── App.jsx                 # 路由配置
│   └── main.jsx
├── index.html
├── vite.config.js
└── package.json
```

---

## 6. 各层关系说明

```
┌─────────────┐
│   前端层     │  只关心 JSON 结构，通过 Axios 调用 API
└──────┬──────┘
       │ HTTP
┌──────▼──────┐
│   API 层     │  参数校验（Pydantic）、路由、HTTP 状态码
└──────┬──────┘
       │ 调用 Service
┌──────▼──────┐
│   服务层     │  业务编排：导入、分析、任务生成、Dashboard 聚合
└──────┬──────┘
       │ 调用 Repository + Rules
┌──────▼──────┐
│ Repository  │  SQLAlchemy 查询/写入，不含业务规则
└──────┬──────┘
       │ ORM
┌──────▼──────┐
│   数据层     │  MySQL 6 张表
└─────────────┘

Rules Engine（utils/agent_rules.py）被 Service 调用，不经过 Repository
```

**依赖方向**：API → Service → Repository → DB；Service → Rules（纯函数）

---

## 7. Excel 模拟数据如何进入 MySQL

### 7.1 Excel 文件规划

| 文件名 | 对应表 |
|--------|--------|
| `product_master.xlsx` | amazon_product_master |
| `inventory_snapshot.xlsx` | amazon_inventory_snapshot |
| `sales_summary.xlsx` | amazon_sales_summary |
| `replenishment_config.xlsx` | inventory_replenishment_config |

### 7.2 导入流程

1. `excel_parser.py` 用 pandas 读取 xlsx，列名与表字段 snake_case 一一对应
2. `import_service.py` 校验必填字段、类型转换
3. 库存快照导入时自动生成 `sync_batch_id`（如 `batch_20250525_001`）和 `sync_time`
4. `repository` 批量 insert（`bulk_insert_mappings`）
5. 商品表 upsert 逻辑：按 `seller_id + marketplace_id + seller_sku` 判断更新或插入

### 7.3 命令入口

```bash
cd backend
python scripts/import_excel.py --data-dir ./data/mock
```

---

## 8. MySQL 数据如何被 Agent 分析

### 8.1 数据选取策略

对每个 `seller_id + marketplace_id + seller_sku`：

| 数据 | 选取规则 |
|------|---------|
| 商品主数据 | `amazon_product_master`，`is_deleted = 0` |
| 库存快照 | `amazon_inventory_snapshot` 按 `sync_time DESC` 取最新一条 |
| 销量汇总 | `amazon_sales_summary` 按 `stat_date DESC` 取最新一条 |
| 补货配置 | `inventory_replenishment_config` 按 `config_status = 'complete'` 取一条 |

### 8.2 分析编排（agent_service.py）

```
1. 生成 analysis_batch_id = "analysis_YYYYMMDD_HHMMSS"
2. 遍历所有有效 SKU
3. 对每个 SKU：
   a. 组装 AgentInput（库存、销量、配置字段）
   b. 调用 agent_rules.analyze_sku(input) → AgentOutput
   c. 写入 inventory_agent_analysis（含三个来源 ID）
4. 调用 task_service.generate_tasks(analysis_batch_id)
5. 返回批次统计（总数、critical 数、任务数）
```

---

## 9. Agent 分析结果如何生成任务

```
inventory_agent_analysis（一批次多条）
        │
        │  task_service.generate_tasks()
        ▼
按规则判断是否需要任务：
  - stockout_risk_level ∈ {critical, high}
  - overstock_risk_level = high
  - total_unfulfillable_quantity > 0（需关联 snapshot）
  - data_quality_status ≠ complete
        │
        ▼
inventory_agent_tasks
  - task_id = UUID
  - task_type 按规则映射
  - priority 按 risk_level 映射
  - task_status = pending
```

任务与分析通过 `analysis_id` 关联，可追溯。

---

## 10. 前端如何展示分析结果和任务

### 10.1 库存总览（Dashboard）

| 指标 | API | 计算方式 |
|------|-----|---------|
| 总 SKU 数 | `GET /api/v1/inventory/overview` | 有效商品数 |
| 断货 critical 数 | 同上 | `stockout_risk_level = critical` 计数 |
| 今日待办数 | 同上 | `task_status = pending` 且 `created_at = today` |
| 滞销 high 数 | 同上 | `overstock_risk_level = high` 计数 |

### 10.2 库存列表（InventoryList）

- 调用 `GET /api/v1/agent/analysis?batch_id=latest`
- 表格列：seller_sku、product_name、fulfillable_quantity、available_days、stockout_risk、overstock_risk、recommended_action
- 支持按 risk_level 筛选

### 10.3 今日待办（TodayTasks）

- 调用 `GET /api/v1/tasks?status=pending&sort=priority`
- 展示：task_title、priority、risk_level、suggested_action
- 操作：标记 `in_progress` / `resolved`

---

## 附录：技术栈对照

| 层级 | 技术 |
|------|------|
| 前端 | React 18、Vite 5、Axios |
| API | FastAPI、Pydantic v2、Uvicorn |
| ORM | SQLAlchemy 2.x |
| DB 驱动 | PyMySQL |
| 数据处理 | pandas、openpyxl |
| 配置 | python-dotenv |
| 数据库 | MySQL 8.x |
