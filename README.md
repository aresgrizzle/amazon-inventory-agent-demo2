# Amazon Inventory Agent Demo

一个面向 Amazon 跨境电商库存运营场景的规则驱动库存 Agent MVP Demo。

项目已经完成从模拟数据、MySQL 入库、库存风险分析、任务生成、FastAPI API 到 React 前端展示的完整闭环。它不是简单 CRUD 项目，而是一个系统级库存 Agent 原型。

## 功能概览

- 生成 30 个 SKU 的模拟 Excel 数据
- 导入商品、库存、销量、补货配置到 MySQL
- 基于规则引擎计算断货风险、滞销风险和补货建议
- 自动生成运营任务
- 提供 FastAPI 接口和 Swagger 文档
- 提供 React + Vite 前端控制台
- 支持 Dashboard、库存分析列表、任务列表、SKU 详情
- 支持任务解决、忽略和重新运行库存 Agent

## 技术栈

后端：

- Python
- FastAPI
- SQLAlchemy
- PyMySQL
- pandas
- openpyxl
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
```

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

## 线上部署

后端启动命令：

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT
```

前端需要配置环境变量：

```text
VITE_API_BASE_URL=https://your-backend-domain.com
```

后端需要配置环境变量：

```text
DB_HOST=your-db-host
DB_PORT=3306
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_NAME=amazon_inventory_agent
CORS_ALLOW_ORIGINS=https://your-frontend-domain.com
```

## 当前阶段

当前项目处于本地可运行、可部署到云端的 MVP Demo 阶段。

尚未包含：

- 真实 Amazon SP-API
- LLM 大模型分析
- 用户登录
- 多租户
- 权限系统
- 自动调度
- SaaS 化部署

## 说明

本项目当前是规则驱动 Agent，不依赖大模型。规则引擎负责计算库存风险、补货建议和运营任务，后续可以扩展为“规则引擎 + LLM 解释层 + AI Copilot”的跨境电商智能运营系统。

