# Amazon Inventory Agent Demo — Cursor 开发行动指南

本文档为 Cursor AI 逐步开发的实操手册。每一步包含：目标、可复制 Prompt、验证命令、需检查的文件、约束提醒。

---

## 全局约束（每一步都要遵守）

1. **不得擅自修改** `docs/database_design.md` 中的表名和字段名
2. 所有字段使用 **snake_case**
3. 第一阶段 **不接 LLM、不接 SP-API、不用 Celery/Docker**
4. 完成后必须输出：**修改文件列表** + **运行方式** + **自检结果**
5. 代码分层：API → Service → Repository，规则放 `utils/agent_rules.py`

---

## Step 0：确认文档已就绪（人工）

### 你应该检查的文件

- `docs/product_plan.md`
- `docs/system_architecture.md`
- `docs/database_design.md`
- `docs/agent_rules.md`
- `docs/development_plan.md`
- `docs/cursor_workflow.md`
- `README.md`

### 验证

```bash
ls docs/
# 应看到 6 个 md 文件
```

---

## Step 0.5：文档一致性修正（每次进入代码开发前建议执行）

### 让 Cursor 做什么

对照 `docs/database_design.md` 与 `docs/agent_rules.md`，检查文档间是否一致；**不写代码**。

### 检查清单

- [ ] 6 张表名、核心字段名未被擅自修改
- [ ] DDL 路径统一为 `backend/sql/01_create_tables.sql`
- [ ] 状态枚举与附录 B 一致（data_quality_status、task_status、config_status、risk_level）
- [ ] MVP 范围：Excel 数据源、规则引擎、不接 LLM / SP-API
- [ ] `agent_rules.md` 不引用数据库中不存在的字段（如 unit_cost）
- [ ] `total_unfulfillable_quantity` 明确来自 `amazon_inventory_snapshot`

### 复制给 Cursor 的 Prompt

```
请阅读 docs/database_design.md 附录 B 和 docs/agent_rules.md。

任务：仅做文档一致性检查，不写 SQL/Python/前端代码。

检查项：
1. 字段名、表名、DDL 路径是否跨文档一致
2. 枚举值是否在 database_design 与 agent_rules 中一致
3. agent_rules 是否引用了不存在的表字段

输出：不一致项列表；若无问题，回复「文档一致，可进入下一步」。
```

### 验证命令

```bash
# 确认 DDL 路径引用
rg "init_tables|01_create_tables" docs/ README.md
# 应仅有 01_create_tables.sql，不应再有 init_tables.sql
```

---

## Step 1：初始化项目目录结构（Milestone 1）

### 让 Cursor 做什么

创建 backend / frontend 空目录骨架、requirements.txt、.env.example、空 __init__.py。**不写业务逻辑**。

### 复制给 Cursor 的 Prompt

```
请阅读 amazon_inventory_agent/docs/system_architecture.md 和 docs/development_plan.md 的 Milestone 1。

任务：初始化项目目录结构，不写任何业务逻辑代码。

要求：
1. 严格按照 system_architecture.md 中的目录结构创建空目录和占位文件
2. 创建 backend/requirements.txt，包含：fastapi, uvicorn[standard], sqlalchemy, pymysql, pandas, openpyxl, python-dotenv, pydantic, pydantic-settings, pytest, httpx
3. 创建 backend/.env.example（参考 development_plan.md 附录）
4. 创建 backend/app/__init__.py 及各子包 __init__.py
5. 创建 frontend/package.json 占位（react, react-dom, vite, axios）
6. 不要创建业务代码文件（main.py 可留空或仅 health check 占位）

约束：
- 不要修改 docs/ 下任何文档
- 不要修改数据库字段名

完成后请输出：
1. 创建/修改的文件列表
2. 目录树
3. 自检：目录是否与 architecture 文档一致
```

### 验证命令

```bash
cd amazon_inventory_agent
find . -name "*.py" -o -name "requirements.txt" -o -name ".env.example" | sort
```

### 你应该检查的文件

- [ ] `backend/requirements.txt`
- [ ] `backend/.env.example`
- [ ] `backend/app/core/`、`api/`、`services/`、`repositories/`、`schemas/`、`utils/` 目录存在
- [ ] `frontend/package.json` 存在

---

## Step 2：编写 MySQL 建表 SQL（Milestone 2）

### 复制给 Cursor 的 Prompt

```
请阅读 docs/database_design.md 全文。

任务：根据数据库设计文档编写建表 SQL 和初始化脚本。

要求：
1. 创建 backend/sql/01_create_tables.sql，包含 6 张表的完整 DDL
2. 表名和字段名必须与 database_design.md 完全一致，不得增删改字段名
3. 不使用 FOREIGN KEY 约束
4. 创建 backend/scripts/init_db.py，读取 .env 中的 DATABASE_URL 执行 SQL
5. 创建 backend/app/core/config.py 和 database.py（SQLAlchemy engine + SessionLocal）

约束：
- 字段类型、索引名、默认值必须与 database_design.md 一致
- amazon_inventory_snapshot 不要加 SKU 唯一索引

完成后请输出：
1. 修改文件列表
2. 运行方式：pip install + python scripts/init_db.py
3. 自检：对照 database_design.md 逐表核对字段
```

### 验证命令

```bash
cd backend
pip install -r requirements.txt
# 配置 .env 后
python scripts/init_db.py

mysql -u root -p amazon_inventory_agent -e "SHOW TABLES;"
mysql -u root -p amazon_inventory_agent -e "DESCRIBE amazon_product_master;"
mysql -u root -p amazon_inventory_agent -e "DESCRIBE inventory_agent_analysis;"
```

### 你应该检查的文件

- [ ] `backend/sql/01_create_tables.sql` — 6 张表、字段完整
- [ ] `backend/scripts/init_db.py` — 可执行
- [ ] `backend/app/core/config.py`
- [ ] `backend/app/core/database.py`

### 字段核对清单

对照 `database_design.md`，每张表逐字段检查 id、seller_id、marketplace_id、seller_sku 等核心字段是否存在。

---

## Step 3：生成模拟 Excel 数据（Milestone 3）

### 复制给 Cursor 的 Prompt

```
请阅读 docs/database_design.md 和 docs/agent_rules.md 的测试用例附录。

任务：创建 Excel 模拟数据生成脚本和模板。

要求：
1. 创建 backend/scripts/generate_mock_excel.py
2. 生成 4 份文件到 backend/data/mock/：
   - product_master.xlsx
   - inventory_snapshot.xlsx
   - sales_summary.xlsx
   - replenishment_config.xlsx
3. Excel 列名必须与数据库字段名一致（snake_case）
4. 约 25 个 SKU，覆盖以下场景：
   - 5 个 critical 断货（fulfillable=0 或 available_days < safety_stock_days）
   - 5 个 high 断货风险
   - 5 个滞销（零销量或 total_cover_days >= 90）
   - 3 个缺补货配置
   - 3 个零销量
5. seller_id 统一为 SELLER_DEMO_001，marketplace_id 为 ATVPDKIKX0DER
6. 同时在 backend/data/templates/ 生成空模板（仅列头）

约束：
- 列名不得自创，必须来自 database_design.md
- 不修改 docs/

完成后请输出文件列表、运行命令、自检（pandas 读取验证）
```

### 验证命令

```bash
cd backend
python scripts/generate_mock_excel.py
python -c "import pandas as pd; df=pd.read_excel('data/mock/product_master.xlsx'); print(df.columns.tolist()); print(len(df))"
```

### 你应该检查的文件

- [ ] `backend/scripts/generate_mock_excel.py`
- [ ] `backend/data/mock/*.xlsx`（4 份）
- [ ] 列名与数据库字段一致

---

## Step 4：实现 Excel 导入 MySQL（Milestone 4）

### 复制给 Cursor 的 Prompt

```
请阅读 docs/system_architecture.md 第 7 节和 docs/database_design.md。

任务：实现 Excel 导入 MySQL 功能。

要求：
1. backend/app/utils/excel_parser.py — pandas 读取 xlsx
2. backend/app/services/import_service.py — 校验 + 导入逻辑
3. backend/app/repositories/ — product_repo, inventory_repo, sales_repo, config_repo
4. backend/scripts/import_excel.py — CLI 入口，支持 --data-dir 参数
5. 库存快照导入时自动生成 sync_batch_id（格式 batch_YYYYMMDD_HHMMSS）和 sync_time
6. 商品表按 seller_id+marketplace_id+seller_sku upsert
7. 库存快照只 insert 不 update（保留历史）

约束：
- 不得修改表名和字段名
- Repository 只做 CRUD，不含业务规则

完成后请输出文件列表、运行命令、自检结果。
```

### 验证命令

```bash
cd backend
python scripts/import_excel.py --data-dir ./data/mock

mysql -u root -p amazon_inventory_agent -e "
SELECT 'products' AS t, COUNT(*) AS c FROM amazon_product_master
UNION ALL SELECT 'snapshots', COUNT(*) FROM amazon_inventory_snapshot
UNION ALL SELECT 'sales', COUNT(*) FROM amazon_sales_summary
UNION ALL SELECT 'configs', COUNT(*) FROM inventory_replenishment_config;
"

# 测试历史批次：再导入一次
python scripts/import_excel.py --data-dir ./data/mock
mysql -u root -p amazon_inventory_agent -e "
SELECT sync_batch_id, COUNT(*) FROM amazon_inventory_snapshot GROUP BY sync_batch_id;
"
```

### 你应该检查的文件

- [ ] `backend/app/utils/excel_parser.py`
- [ ] `backend/app/services/import_service.py`
- [ ] `backend/app/repositories/*.py`
- [ ] `backend/scripts/import_excel.py`

---

## Step 5：实现 Agent 规则函数（Milestone 5）

### 复制给 Cursor 的 Prompt

```
请阅读 docs/agent_rules.md 全文。

任务：实现库存 Agent 规则引擎纯函数。

要求：
1. 创建 backend/app/utils/agent_rules.py
2. 实现全部规则：available_days, total_cover_days, effective_inbound, estimated_stockout_date, stockout_risk, overstock_risk, recommended_replenishment_quantity, recommended_action, data_quality_status, confidence_score
3. 使用 AgentInput / AgentOutput Pydantic 模型（可放同文件或 schemas/agent.py）
4. 创建 backend/tests/test_agent_rules.py，覆盖 agent_rules.md 附录 R01-R08 用例
5. 函数无副作用，不访问数据库

约束：
- 规则逻辑必须与 agent_rules.md 完全一致
- 输出字段名与 inventory_agent_analysis 表字段一致

完成后请输出文件列表，运行 pytest 并报告结果。
```

### 验证命令

```bash
cd backend
pytest tests/test_agent_rules.py -v --tb=short
```

### 你应该检查的文件

- [ ] `backend/app/utils/agent_rules.py`
- [ ] `backend/tests/test_agent_rules.py`
- [ ] 全部测试 PASS

---

## Step 6：实现 Agent 分析服务（Milestone 6）

### 复制给 Cursor 的 Prompt

```
请阅读 docs/system_architecture.md 第 8 节和 docs/agent_rules.md。

任务：实现 Agent 分析编排服务。

要求：
1. backend/app/services/agent_service.py
   - 生成 analysis_batch_id
   - 遍历所有有效 SKU（is_deleted=0, listing_status=Active）
   - 取最新 inventory_snapshot、sales_summary、replenishment_config
   - 调用 agent_rules.analyze_sku()
   - 写入 inventory_agent_analysis（含三个来源 ID）
2. backend/app/repositories/analysis_repo.py
3. backend/app/schemas/agent.py
4. backend/scripts/run_agent_analysis.py

约束：
- 字段名不得修改
- 缺数据时仍要生成分析记录，标记 data_quality_status

完成后请输出文件列表、运行命令、自检（SQL 查询 critical 数量）。
```

### 验证命令

```bash
cd backend
python scripts/run_agent_analysis.py

mysql -u root -p amazon_inventory_agent -e "
SELECT stockout_risk_level, COUNT(*) FROM inventory_agent_analysis
GROUP BY stockout_risk_level;
SELECT seller_sku, stockout_risk_level, available_days, recommended_action
FROM inventory_agent_analysis WHERE stockout_risk_level='critical' LIMIT 5;
"
```

### 你应该检查的文件

- [ ] `backend/app/services/agent_service.py`
- [ ] `backend/app/repositories/analysis_repo.py`
- [ ] `backend/scripts/run_agent_analysis.py`
- [ ] analysis 表有数据，critical SKU 正确

---

## Step 7：实现任务生成服务（Milestone 7）

### 复制给 Cursor 的 Prompt

```
请阅读 docs/agent_rules.md 第 9 节（任务生成规则）。

任务：实现任务生成服务。

要求：
1. backend/app/services/task_service.py
   - generate_tasks(analysis_batch_id) 方法
   - 按规则生成 5 种 task_type
   - task_id 使用 uuid4
   - action_parameters 为 JSON
2. backend/app/repositories/task_repo.py
3. backend/app/schemas/task.py
4. 在 run_agent_analysis.py 中分析完成后自动调用任务生成

约束：
- task_type、task_status 枚举值与 database_design.md 一致
- 不得修改表字段名

完成后请输出文件列表、运行命令、自检 SQL。
```

### 验证命令

```bash
cd backend
python scripts/run_agent_analysis.py

mysql -u root -p amazon_inventory_agent -e "
SELECT task_type, priority, COUNT(*) FROM inventory_agent_tasks GROUP BY task_type, priority;
SELECT task_title, task_status FROM inventory_agent_tasks LIMIT 5;
"
```

### 你应该检查的文件

- [ ] `backend/app/services/task_service.py`
- [ ] `backend/app/repositories/task_repo.py`
- [ ] 任务表有 pending 状态记录

---

## Step 8：实现 FastAPI 接口（Milestone 8）

### 复制给 Cursor 的 Prompt

```
请阅读 docs/system_architecture.md 和 docs/development_plan.md Milestone 8 的 API 端点清单。

任务：实现 FastAPI REST API。

要求：
1. backend/app/main.py — 注册路由、CORS、health check
2. backend/app/api/deps.py — get_db 依赖注入
3. backend/app/api/v1/inventory.py — GET /overview
4. backend/app/api/v1/agent.py — GET /analysis, GET /analysis/{id}, POST /analyze
5. backend/app/api/v1/tasks.py — GET /tasks, GET /tasks/{task_id}, PATCH /tasks/{task_id}
6. backend/app/services/dashboard_service.py — 总览聚合
7. 所有响应使用 Pydantic schema，字段 snake_case

约束：
- API 层只调用 Service，不直接写 SQL
- 不修改数据库字段名

完成后请输出文件列表、启动命令、curl 测试示例、自检结果。
```

### 验证命令

```bash
cd backend
uvicorn app.main:app --reload --port 8000

# 另开终端
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/inventory/overview
curl "http://localhost:8000/api/v1/agent/analysis?limit=5"
curl "http://localhost:8000/api/v1/tasks?status=pending&limit=5"
curl -X POST http://localhost:8000/api/v1/agent/analyze
```

### 你应该检查的文件

- [ ] `backend/app/main.py`
- [ ] `backend/app/api/v1/*.py`
- [ ] Swagger http://localhost:8000/docs 可访问
- [ ] 所有端点返回 JSON，无 500 错误

---

## Step 9：实现 React 前端（Milestone 9）

### 复制给 Cursor 的 Prompt

```
请阅读 docs/system_architecture.md 第 5、10 节。

任务：实现 React + Vite 前端三个页面。

要求：
1. 初始化 Vite React 项目（如未初始化）
2. frontend/src/api/ — Axios 封装，baseURL 指向 http://localhost:8000
3. frontend/vite.config.js — 配置 proxy /api -> localhost:8000
4. 三个页面：
   - Dashboard.jsx — 4 个指标卡片（总SKU、critical数、待办数、滞销数）
   - InventoryList.jsx — 分析结果表格，风险等级彩色标签
   - TodayTasks.jsx — 待办列表，可更新任务状态
5. App.jsx — React Router 路由
6. 组件：Layout, StatCard, RiskBadge, InventoryTable, TaskTable

约束：
- 前端不做业务计算，全部从 API 获取
- 不修改后端字段名

完成后请输出文件列表、npm run dev 启动方式、自检（三个页面截图描述）。
```

### 验证命令

```bash
# 确保后端运行中
cd frontend
npm install
npm run dev
# 浏览器访问 http://localhost:5173
```

### 你应该检查的文件

- [ ] `frontend/src/pages/Dashboard.jsx`
- [ ] `frontend/src/pages/InventoryList.jsx`
- [ ] `frontend/src/pages/TodayTasks.jsx`
- [ ] `frontend/src/api/*.js`
- [ ] 三个页面数据正常显示，无 console 报错

---

## Step 10：数据质量检查（Milestone 10）

### 复制给 Cursor 的 Prompt

```
请阅读 docs/agent_rules.md 第 10 节和 docs/development_plan.md Milestone 10。

任务：实现数据质量检查。

要求：
1. backend/app/services/data_quality_service.py
2. backend/scripts/check_data_quality.py
3. GET /api/v1/data-quality/report 端点
4. 报告包含：missing_sales_count, missing_config_count, missing_inventory_count, complete_count

约束：
- 不修改表结构

完成后请输出文件列表、运行命令、自检。
```

### 验证命令

```bash
cd backend
python scripts/check_data_quality.py
curl http://localhost:8000/api/v1/data-quality/report
```

---

## 全流程验收（前端完成后）

### 一键跑通命令

```bash
# 1. 建表
cd backend && python scripts/init_db.py

# 2. 生成并导入数据
python scripts/generate_mock_excel.py
python scripts/import_excel.py --data-dir ./data/mock

# 3. Agent 分析 + 任务生成
python scripts/run_agent_analysis.py

# 4. 启动后端
uvicorn app.main:app --reload --port 8000

# 5. 启动前端（新终端）
cd ../frontend && npm run dev
```

### 最终验收清单

- [ ] 6 张表有数据
- [ ] Agent 分析有 critical / high / low 分布
- [ ] 任务表有 pending 任务
- [ ] API 全部端点正常
- [ ] 前端三个页面正常展示
- [ ] 全流程 30 分钟内可跑通

---

## 常见问题：Cursor 擅自改字段时

### 复制给 Cursor 的 Prompt

```
停止。请对照 docs/database_design.md 恢复以下字段名：[列出被改的字段]。
不得自创字段名。修改后重新运行验证命令并输出 diff。
```

---

## 附录：每步 Cursor 必须输出的格式

```
## 本步完成报告

### 修改文件列表
- path/to/file1.py（新建）
- path/to/file2.py（修改）

### 运行方式
```bash
具体命令
```

### 自检结果
- [x] 测试通过 / 验证命令成功
- [ ] 待用户确认的点

### 未修改的约束确认
- 表名/字段名与 database_design.md 一致
```

---

## Step 11：Amazon SP-API 后续接入（占位，Milestone 11）

> **当前阶段不实现**。仅作后续规划，勿生成 SP-API 业务代码。

### 让 Cursor 做什么

阅读 `docs/development_plan.md` Milestone 11，输出接入方案摘要（文档或注释级），不写真实 API 调用代码。

### 复制给 Cursor 的 Prompt

```
请阅读 docs/development_plan.md 的 Milestone 11 和 docs/system_architecture.md。

任务：编写 SP-API 接入规划摘要（可写入 docs/sp_api_integration_plan.md 或仅在回复中输出），不实现代码。

需包含：
1. 拟接入 API：FBA Inventory、Reports、Orders
2. 与现有 6 张表的字段映射关系
3. data_source 字段如何标记为 sp_api
4. 同步频率与批次号（sync_batch_id）策略
5. 对现有 Agent 分析流程的影响（应无破坏性变更）

约束：
- 不修改 6 张核心表名与字段名
- 不写 Python 集成代码
- 不配置真实 LWA 凭证

完成后输出文件列表（若新建 md）与规划摘要。
```

### 验证命令

```bash
# 确认尚未引入 sp-api 代码（应为空或无匹配）
rg "sp_api|SellingPartner" backend/ 2>/dev/null || echo "无 SP-API 代码，符合预期"
```

### 你应该检查的内容

- [ ] 规划与 MVP 表结构兼容
- [ ] 未改动 agent_rules 核心逻辑
- [ ] 未创建 .env 真实密钥
