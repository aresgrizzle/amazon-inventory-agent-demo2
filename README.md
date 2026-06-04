# Amazon Inventory Agent Demo

Amazon Inventory Agent Demo 是一个面向跨境电商库存运营场景的系统级 Agent MVP。项目已经完成从模拟数据、MySQL 入库、规则型库存风险分析、任务生成、FastAPI API 到 React 前端展示的完整闭环。

当前版本加入了 OpenAI AI 运营解释层：规则引擎继续负责风险计算，OpenAI 只负责把系统已经计算出的风险、任务和数据质量结果解释成运营负责人能直接阅读的中文建议。

## 功能概览

- 生成 30 个 SKU 的模拟 Excel 数据。
- 导入商品、库存、销量、补货配置到 MySQL。
- 基于规则引擎计算断货风险、滞销风险和补货建议。
- 自动生成运营任务。
- 提供 FastAPI 接口和 Swagger 文档。
- 提供 React + Vite 前端控制台。
- 支持 Dashboard、库存分析列表、任务列表、SKU 详情。
- 支持任务解决、忽略和重新运行库存 Agent。
- 支持 OpenAI 生成 Dashboard 运营总结、单 SKU 运营解读和任务优先级建议。

## 技术栈

后端：

- Python
- FastAPI
- SQLAlchemy
- PyMySQL
- pandas
- openpyxl
- OpenAI Python SDK
- pytest

前端：

- React
- Vite
- Axios
- CSS

数据库：

- MySQL

## 项目结构

```text
amazon_inventory_agent/
├─ backend/
│  ├─ app/
│  │  ├─ api/
│  │  ├─ core/
│  │  ├─ repositories/
│  │  ├─ schemas/
│  │  ├─ services/
│  │  ├─ utils/
│  │  └─ main.py
│  ├─ scripts/
│  ├─ sql/
│  ├─ tests/
│  ├─ .env.example
│  └─ requirements.txt
├─ docs/
├─ frontend/
│  ├─ src/
│  │  ├─ api/
│  │  ├─ components/
│  │  ├─ pages/
│  │  └─ styles/
│  ├─ .env.example
│  └─ package.json
├─ railway.toml
├─ requirements.txt
└─ README.md
```

## 本地运行

### 1. 创建数据库

```sql
CREATE DATABASE amazon_inventory_agent
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
```

### 2. 执行建表 SQL

```bash
mysql -u root -p amazon_inventory_agent < backend/sql/01_create_tables.sql
```

### 3. 配置后端环境变量

复制示例文件：

```bash
cp backend/.env.example backend/.env
```

填写数据库连接：

```text
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=amazon_inventory_agent
CORS_ALLOW_ORIGINS=http://127.0.0.1:5173
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
AI_ENABLED=false
```

如果暂时不接 OpenAI，保持 `AI_ENABLED=false` 或不填写 `OPENAI_API_KEY` 即可。原有库存分析、任务和前端页面仍然可用。

### 4. 安装后端依赖

```bash
pip install -r backend/requirements.txt
```

### 5. 生成并导入 Demo 数据

```bash
python backend/scripts/generate_demo_excel.py
python backend/scripts/import_demo_data.py
python backend/scripts/run_inventory_agent.py
```

### 6. 启动后端

```bash
uvicorn backend.app.main:app --reload
```

后端地址：

```text
http://127.0.0.1:8000
```

Swagger：

```text
http://127.0.0.1:8000/docs
```

### 7. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端地址：

```text
http://127.0.0.1:5173
```

## 测试

```bash
python -m pytest backend/tests/test_inventory_rules.py
```

前端构建：

```bash
cd frontend
npm run build
```

## OpenAI AI 运营解释层

AI 相关接口：

```text
GET /api/ai/dashboard-summary
GET /api/ai/sku-analysis/{seller_sku}
GET /api/ai/task-priority
```

未配置 OpenAI 时，接口返回：

```json
{
  "configured": false,
  "message": "OpenAI is not configured"
}
```

配置 OpenAI 后，接口会返回中文运营分析内容。AI 不会重新计算库存风险，只解释系统已经计算出的规则结果。

## 线上部署

后端 Railway 启动命令：

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

Railway 后端环境变量：

```text
DB_HOST=your-db-host
DB_PORT=3306
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=your-db-name
CORS_ALLOW_ORIGINS=https://your-frontend-domain.vercel.app
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
AI_ENABLED=true
```

OpenAI API Key 只能配置在 Railway 后端，不能放到 Vercel 前端。

Vercel 前端环境变量：

```text
VITE_API_BASE_URL=https://your-backend-domain.up.railway.app
```

Vercel 不需要配置 OpenAI API Key。

## 当前阶段

当前项目处于可公网访问的 MVP Demo 阶段，已经具备：

- 数据层
- 规则分析层
- AI 运营解释层
- 任务层
- API 层
- 前端可视化层

尚未包含：

- 真实 Amazon SP-API
- 多租户授权
- 用户登录
- 权限系统
- 自动调度
- AI 输出入库
- SaaS 化计费和部署体系

## 说明

本项目不是简单 CRUD Demo，而是一个规则驱动库存 Agent 加 AI 解释层的运营系统原型。规则引擎负责确定性计算，OpenAI 负责将计算结果转化为运营团队可读的总结、复盘和处理建议。
