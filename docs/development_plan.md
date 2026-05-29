# Amazon Inventory Agent Demo — 开发计划（Harness Engineering）

## Harness Engineering 说明

本项目采用 Harness Engineering 思路：将开发过程拆分为**可验证的步骤（Harness Steps）**，每一步都有明确的：

- **输入（Input）**：上一步产出或前置条件
- **输出（Output）**：本步交付物
- **运行命令（Run）**：可复制的执行命令
- **验收标准（Acceptance）**：通过/不通过的判定条件

后续 Cursor 开发时，严格按 Milestone 顺序执行，不跳步、不擅自改字段名。

---

## Milestone 总览

| # | 名称 | 预估工时 |
|---|------|---------|
| M1 | 项目文档与目录初始化 | 0.5h |
| M2 | MySQL 建表 SQL | 1h |
| M3 | 模拟 Excel 数据生成 | 1h |
| M4 | Excel 导入 MySQL | 2h |
| M5 | 库存 Agent 规则函数 | 2h |
| M6 | 库存 Agent 分析服务 | 2h |
| M7 | 任务生成服务 | 1.5h |
| M8 | FastAPI 接口 | 2h |
| M9 | React 前端页面 | 3h |
| M10 | 数据质量检查 | 1h |
| M11 | 接入真实 Amazon SP-API | 后续 |

---

## Milestone 1：项目文档与目录初始化

### 目标

创建完整项目文档与空目录骨架，为后续代码开发提供引用基准。

### 输入

- 本规划文档集（product_plan、architecture、database、agent_rules 等）

### 输出

- `docs/` 下 6 份文档 + `README.md`
- `backend/`、`frontend/` 空目录结构
- `backend/.env.example`
- `backend/requirements.txt`（仅依赖列表，无业务代码）
- `frontend/package.json`（仅脚手架占位）

### 需要创建或修改的文件

```
amazon_inventory_agent/
├── docs/（6 份 md + 本文件）
├── README.md
├── backend/
│   ├── app/__init__.py
│   ├── .env.example
│   └── requirements.txt
└── frontend/
    └── package.json（占位）
```

### 运行命令

```bash
# 验证目录结构
tree amazon_inventory_agent /F   # Windows
# 或
find amazon_inventory_agent -type f | head -30
```

### 验收标准

- [ ] 7 个文档文件全部存在且内容为中文
- [ ] 目录结构与 `system_architecture.md` 一致
- [ ] `requirements.txt` 包含：fastapi, uvicorn, sqlalchemy, pymysql, pandas, openpyxl, python-dotenv, pydantic
- [ ] 无业务逻辑代码（允许空 `__init__.py`）

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| 目录已存在 | 跳过创建，检查文件完整性 |
| 文档与代码字段不一致 | 以 `database_design.md` 为准 |

---

## Milestone 2：MySQL 建表 SQL

### 目标

根据 `database_design.md` 编写 6 张表的 DDL，支持一键初始化数据库。

### 输入

- `docs/database_design.md`
- 本地 MySQL 8.x 实例
- `backend/.env` 中的 `DATABASE_URL`

### 输出

- `backend/sql/01_create_tables.sql`
- `backend/scripts/init_db.py`

### 需要创建或修改的文件

```
backend/sql/01_create_tables.sql
backend/scripts/init_db.py
backend/app/core/config.py
backend/app/core/database.py
```

### 运行命令

```bash
# 1. 配置环境变量
cp backend/.env.example backend/.env
# 编辑 .env：DATABASE_URL=mysql+pymysql://user:pass@localhost:3306/amazon_inventory_agent

# 2. 创建数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS amazon_inventory_agent CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 3. 安装依赖
cd backend && pip install -r requirements.txt

# 4. 执行建表
python scripts/init_db.py
```

### 验收标准

- [ ] 6 张表全部创建成功
- [ ] 表名、字段名与 `database_design.md` 完全一致（snake_case）
- [ ] 无外键约束
- [ ] `amazon_inventory_snapshot` 无 SKU 级别唯一索引（允许历史）
- [ ] `amazon_product_master` 有 `uk_seller_marketplace_sku` 唯一索引
- [ ] 执行 `SHOW TABLES;` 返回 6 张表

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| MySQL 连接失败 | 检查 .env、MySQL 服务、用户权限 |
| JSON 类型不支持 | 确认 MySQL >= 5.7.8，tasks 表 `action_parameters` 用 JSON |
| 字符集问题 | 统一 utf8mb4_unicode_ci |

---

## Milestone 3：模拟 Excel 数据生成

### 目标

生成 4 份 Excel 模拟数据，覆盖正常、断货、滞销、数据缺失等场景。

### 输入

- `docs/database_design.md` 字段定义
- `docs/agent_rules.md` 测试场景

### 输出

- `backend/data/templates/` 空模板（含列头）
- `backend/data/mock/` 模拟数据（约 20–30 个 SKU）
- `backend/scripts/generate_mock_excel.py`

### 需要创建或修改的文件

```
backend/data/templates/product_master.xlsx
backend/data/templates/inventory_snapshot.xlsx
backend/data/templates/sales_summary.xlsx
backend/data/templates/replenishment_config.xlsx
backend/data/mock/（4 份填充好的 xlsx）
backend/scripts/generate_mock_excel.py
```

### 运行命令

```bash
cd backend
python scripts/generate_mock_excel.py
# 检查输出
ls data/mock/
```

### 验收标准

- [ ] 4 份 xlsx 文件生成成功
- [ ] 列名与数据库字段名一致（snake_case）
- [ ] 至少包含：5 个 critical 断货 SKU、5 个 high 风险 SKU、5 个滞销 SKU、3 个缺配置 SKU、3 个零销量 SKU
- [ ] `seller_id`、`marketplace_id` 统一（如 `SELLER_DEMO_001` / `ATVPDKIKX0DER`）
- [ ] 用 pandas 可正常读取，无空列头

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| openpyxl 未安装 | pip install openpyxl |
| 日期格式错误 | 统一 YYYY-MM-DD |
| 中文乱码 | 保存为 UTF-8 兼容格式 |

---

## Milestone 4：Excel 导入 MySQL

### 目标

实现 Excel → MySQL 导入，库存快照带 `sync_batch_id` 保留历史。

### 输入

- M2 建表完成
- M3 模拟 Excel 文件

### 输出

- `backend/app/utils/excel_parser.py`
- `backend/app/services/import_service.py`
- `backend/app/repositories/`（4 个 repo）
- `backend/scripts/import_excel.py`
- MySQL 中有数据

### 需要创建或修改的文件

```
backend/app/utils/excel_parser.py
backend/app/services/import_service.py
backend/app/repositories/product_repo.py
backend/app/repositories/inventory_repo.py
backend/app/repositories/sales_repo.py
backend/app/repositories/config_repo.py
backend/scripts/import_excel.py
```

### 运行命令

```bash
cd backend
python scripts/import_excel.py --data-dir ./data/mock

# 验证数据
mysql -u root -p amazon_inventory_agent -e "
  SELECT COUNT(*) AS products FROM amazon_product_master;
  SELECT COUNT(*) AS snapshots FROM amazon_inventory_snapshot;
  SELECT COUNT(*) AS sales FROM amazon_sales_summary;
  SELECT COUNT(*) AS configs FROM inventory_replenishment_config;
"
```

### 验收标准

- [ ] 4 张源表均有数据，行数与 Excel 一致
- [ ] `amazon_inventory_snapshot.sync_batch_id` 非空
- [ ] 重复导入生成新 batch，不覆盖旧快照
- [ ] `amazon_product_master` 重复 SKU 执行 upsert
- [ ] 导入脚本支持 `--data-dir` 参数
- [ ] 无报错退出码 0

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| 列名不匹配 | 对照 database_design.md 修正 Excel 或 parser |
| 批量插入慢 | 使用 bulk_insert_mappings，每批 500 条 |
| DECIMAL 精度 | SQLAlchemy Numeric(10,2) |

---

## Milestone 5：库存 Agent 规则函数

### 目标

实现 `agent_rules.py` 全部纯函数，附完整单元测试。

### 输入

- `docs/agent_rules.md`
- M4 数据库中有测试数据（可选，单元测试用 mock）

### 输出

- `backend/app/utils/agent_rules.py`
- `backend/tests/test_agent_rules.py`

### 需要创建或修改的文件

```
backend/app/utils/agent_rules.py
backend/tests/test_agent_rules.py
```

### 运行命令

```bash
cd backend
pytest tests/test_agent_rules.py -v
```

### 验收标准

- [ ] 全部 8+ 条规则有对应函数
- [ ] `test_agent_rules.py` 至少 8 个用例全部 PASS
- [ ] R01–R08 附录用例覆盖
- [ ] 函数无副作用，不访问数据库
- [ ] 输出字段名与 `inventory_agent_analysis` 表字段一致

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| Decimal 除法精度 | 使用 Decimal 类型，round 到 2 位 |
| available_days 为 None | 后续规则需判空 |
| 箱规取整 | math.ceil |

---

## Milestone 6：库存 Agent 分析服务

### 目标

编排数据读取 + 规则调用 + 结果写入 `inventory_agent_analysis`。

### 输入

- M4 数据已导入
- M5 规则函数完成

### 输出

- `backend/app/services/agent_service.py`
- `backend/app/repositories/analysis_repo.py`
- `backend/scripts/run_agent_analysis.py`
- `inventory_agent_analysis` 表有数据

### 需要创建或修改的文件

```
backend/app/services/agent_service.py
backend/app/repositories/analysis_repo.py
backend/app/schemas/agent.py
backend/scripts/run_agent_analysis.py
```

### 运行命令

```bash
cd backend
python scripts/run_agent_analysis.py

# 验证
mysql -u root -p amazon_inventory_agent -e "
  SELECT analysis_batch_id, COUNT(*) AS cnt,
         SUM(stockout_risk_level='critical') AS critical_cnt
  FROM inventory_agent_analysis
  GROUP BY analysis_batch_id
  ORDER BY created_at DESC LIMIT 1;
"
```

### 验收标准

- [ ] 每个有效 SKU 有一条分析记录
- [ ] `analysis_batch_id` 统一
- [ ] `inventory_snapshot_id`、`sales_summary_id`、`replenishment_config_id` 正确填充
- [ ] critical SKU 的 `stockout_risk_level = critical`
- [ ] 零销量 SKU 的 `available_days` 为 NULL
- [ ] 脚本可重复运行，生成新批次

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| 找不到最新快照 | 按 sync_time DESC LIMIT 1 |
| SKU 无配置 | data_quality_status = missing_config |
| 性能慢 | 批量查询 + 内存组装，避免 N+1 |

---

## Milestone 7：任务生成服务

### 目标

根据分析结果生成 `inventory_agent_tasks` 记录。

### 输入

- M6 分析批次已完成

### 输出

- `backend/app/services/task_service.py`
- `backend/app/repositories/task_repo.py`
- `inventory_agent_tasks` 表有数据

### 需要创建或修改的文件

```
backend/app/services/task_service.py
backend/app/repositories/task_repo.py
backend/app/schemas/task.py
```

### 运行命令

```bash
cd backend
# 任务生成通常合并在 run_agent_analysis.py 中
python scripts/run_agent_analysis.py --with-tasks

mysql -u root -p amazon_inventory_agent -e "
  SELECT task_type, priority, COUNT(*) AS cnt
  FROM inventory_agent_tasks
  GROUP BY task_type, priority;
"
```

### 验收标准

- [ ] critical 断货 SKU 有 `stockout_warning` 任务
- [ ] high 断货 SKU 有 `replenishment_suggestion` 任务
- [ ] 滞销 SKU 有 `overstock_warning` 任务
- [ ] 缺数据 SKU 有 `data_missing_alert` 任务
- [ ] `task_id` 为 UUID，唯一
- [ ] `task_status` 默认为 pending
- [ ] `action_parameters` 为合法 JSON

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| 重复生成任务 | 按 analysis_batch_id 先删后插，或检查是否已存在 |
| 一 SKU 多任务 | 符合设计，按 task_type 分别生成 |

---

## Milestone 8：FastAPI 接口

### 目标

提供 REST API 供前端和脚本调用。

### 输入

- M6、M7 服务层完成

### 输出

- `backend/app/main.py`
- `backend/app/api/v1/` 路由
- API 可通过 Swagger 访问

### 需要创建或修改的文件

```
backend/app/main.py
backend/app/api/deps.py
backend/app/api/v1/inventory.py
backend/app/api/v1/agent.py
backend/app/api/v1/tasks.py
backend/app/services/dashboard_service.py
```

### 运行命令

```bash
cd backend
uvicorn app.main:app --reload --port 8000

# 测试 API
curl http://localhost:8000/api/v1/inventory/overview
curl http://localhost:8000/api/v1/agent/analysis?limit=10
curl -X POST http://localhost:8000/api/v1/agent/analyze
curl http://localhost:8000/api/v1/tasks?status=pending
```

### 验收标准

- [ ] `GET /docs` Swagger 可访问
- [ ] overview 返回总 SKU、critical 数、待办数
- [ ] analysis 列表支持分页、按 risk 筛选
- [ ] `POST /agent/analyze` 触发分析并返回 batch_id
- [ ] `PATCH /tasks/{task_id}` 可更新 status
- [ ] CORS 允许 `http://localhost:5173`
- [ ] 所有响应字段 snake_case

### API 端点清单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /api/v1/inventory/overview | 库存总览 |
| GET | /api/v1/agent/analysis | 分析结果列表 |
| GET | /api/v1/agent/analysis/{id} | 分析详情 |
| POST | /api/v1/agent/analyze | 触发分析 |
| GET | /api/v1/tasks | 任务列表 |
| GET | /api/v1/tasks/{task_id} | 任务详情 |
| PATCH | /api/v1/tasks/{task_id} | 更新任务状态 |

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| CORS 错误 | 配置 CORSMiddleware |
| 循环导入 | api → service → repo，不反向 |
| 分页 | 使用 limit/offset 参数 |

---

## Milestone 9：React 前端页面

### 目标

实现三个核心页面，对接后端 API。

### 输入

- M8 API 运行中

### 输出

- Vite + React 项目
- 3 个页面可正常展示数据

### 需要创建或修改的文件

```
frontend/src/api/client.js
frontend/src/api/inventory.js
frontend/src/api/agent.js
frontend/src/api/tasks.js
frontend/src/pages/Dashboard.jsx
frontend/src/pages/InventoryList.jsx
frontend/src/pages/TodayTasks.jsx
frontend/src/components/（StatCard, RiskBadge, InventoryTable, TaskTable, Layout）
frontend/src/App.jsx
frontend/vite.config.js（proxy 配置）
```

### 运行命令

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 验收标准

- [ ] Dashboard 显示 4 个指标卡片
- [ ] 库存列表显示 SKU、可售天数、风险等级、建议动作
- [ ] 今日待办显示 pending 任务，可按优先级排序
- [ ] 任务可标记为 in_progress / resolved
- [ ] 断货 critical 行红色高亮
- [ ] 页面无 console 报错
- [ ] API 代理或 VITE_API_BASE_URL 配置正确

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| API 跨域 | vite.config.js proxy 到 8000 |
| 空数据 | 先运行 import + analyze |
| 日期格式 | 前端 format 为本地时间 |

---

## Milestone 10：数据质量检查

### 目标

增加数据质量检查脚本与 API，帮助运营发现数据问题。

### 输入

- M4–M7 全部完成

### 输出

- `backend/scripts/check_data_quality.py`
- `GET /api/v1/data-quality/report` 端点

### 需要创建或修改的文件

```
backend/scripts/check_data_quality.py
backend/app/services/data_quality_service.py
backend/app/api/v1/data_quality.py
```

### 运行命令

```bash
cd backend
python scripts/check_data_quality.py

curl http://localhost:8000/api/v1/data-quality/report
```

### 验收标准

- [ ] 报告列出：无销量 SKU 数、无配置 SKU 数、无库存 SKU 数
- [ ] 与 Agent 分析中 `data_quality_status != complete` 数量一致
- [ ] 脚本退出码：有问题时返回 1（可选）

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| 误报 | 区分「无记录」与「零销量」 |

---

## Milestone 11：接入真实 Amazon SP-API（后续）

### 目标

将 Excel 数据源替换为 SP-API 定时同步（不在 MVP 范围，仅规划）。

### 输入

- Amazon Seller Central 开发者账号
- SP-API LWA 凭证

### 输出

- `backend/app/integrations/sp_api/` 模块
- 定时同步脚本（可用 cron，不用 Celery）

### 需要创建或修改的文件

```
backend/app/integrations/sp_api/client.py
backend/app/integrations/sp_api/inventory_sync.py
backend/app/integrations/sp_api/orders_sync.py
backend/scripts/sync_sp_api.py
```

### 运行命令

```bash
# 后续实现
python scripts/sync_sp_api.py --resource inventory
```

### 验收标准

- [ ] FBA Inventory 数据写入 snapshot 表
- [ ] Orders 数据可计算 sales_summary
- [ ] `data_source` 字段标记为 sp_api
- [ ] Agent 分析流程不变

### 可能遇到的问题

| 问题 | 解决方案 |
|------|---------|
| API 限流 | 加重试与退避 |
| 报告延迟 | Reports API 异步轮询 |

---

## 附录：本地环境要求

| 组件 | 版本要求 |
|------|---------|
| Python | 3.10+ |
| Node.js | 18+ |
| MySQL | 8.0+ |
| pip / npm | 最新稳定版 |

## 附录：.env.example 模板

```env
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/amazon_inventory_agent
SELLER_ID=SELLER_DEMO_001
MARKETPLACE_ID=ATVPDKIKX0DER
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:5173
```
