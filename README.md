# AgentNex

智能代理系统 - 具备工具调用、记忆管理和知识库检索能力

## 功能特性

- **Monorepo 架构**: 使用 pnpm workspace 管理多个应用和共享包
- **AI 对话 Agent**: 集成 agno 和 DashScope (通义千问) 的智能对话功能
- **用户系统**: 完整的用户认证、RBAC 权限、团队管理
- **Agent 管理**: 创建、配置、测试 Agent，支持知识库和工具调用
- **现代化前端栈**: React 19 + TypeScript + Vite + Tailwind CSS
- **UI 组件库**: 基于 shadcn/ui 的可复用组件库

---

## 一、环境准备

确保已安装：

| 依赖 | 版本要求 |
|-----|---------|
| Node.js | >= 18 |
| pnpm | >= 9.0 |
| Python | >= 3.11 |
| PostgreSQL | >= 14 |
| Docker (可选) | 最新版 |

```bash
# 安装 pnpm
npm install -g pnpm

# macOS 安装 PostgreSQL (可选，本地开发需要)
brew install postgresql@14
brew services start postgresql@14
```

---

## 二、配置环境变量

1. 复制示例配置：
```bash
cp .env.example .env
```

2. 编辑 `.env`，填入必填项：
```env
# 必填 - AI 服务
DASHSCOPE_API_KEY=your_dashscope_api_key

# 可选 - 网络搜索
TAVILY_API_KEY=your_tavily_api_key

# 数据库 (本地开发)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=agentnex
POSTGRES_PASSWORD=agentnex123
POSTGRES_DB=agentnex
```

> **获取 API Key**: 访问 [DashScope 控制台](https://dashscope.console.aliyun.com/)

---

## 三、启动方式

### 方式 A：Docker 启动（推荐生产环境）

**适合**: 生产部署、快速体验

```bash
# 一键启动所有服务（PostgreSQL + 后端 + 前端）
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 方式 B：本地开发启动

**适合**: 开发调试

#### 1. 安装依赖

```bash
# 前端依赖
pnpm install

# 后端依赖（创建虚拟环境）
cd agent
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

#### 2. 启动 PostgreSQL

```bash
# macOS (Homebrew)
brew services start postgresql@14

# 创建数据库
createdb agentnex

# 或使用 psql
psql postgres -c "CREATE DATABASE agentnex;"
```

#### 3. 启动后端

```bash
# 在项目根目录，设置 PYTHONPATH
cd /path/to/AgentNex
PYTHONPATH=$(pwd) agent/venv/bin/python -m agent.main
```

#### 4. 启动前端

```bash
cd apps/web
pnpm dev
```

#### 或使用启动脚本

```bash
# macOS
./start-venv.sh
```

---

## 四、访问地址

| 服务 | 地址 |
|-----|------|
| 前端 | http://localhost:5173 |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 管理员账号 | `admin@agentnex.io` |
| 管理员密码 | `AgentNex@2026` |

---

## 五、常见问题

### Q: `ModuleNotFoundError: No module named 'agent'`

**A**: 启动后端时必须设置 `PYTHONPATH`：
```bash
PYTHONPATH=$(pwd) agent/venv/bin/python -m agent.main
```

### Q: 数据库连接失败

**A**: 确保 PostgreSQL 正在运行且数据库已创建：
```bash
# 检查 PostgreSQL 状态
brew services list

# 创建数据库
createdb agentnex
```

### Q: 前端无法连接后端

**A**: 检查 `.env` 中的 `VITE_API_URL` 配置：
```env
VITE_API_URL=http://localhost:8000
```

### Q: 如何查看本地开发日志

**A**:
```bash
# 后端日志
tail -f /tmp/agentnex_backend.log

# 前端日志
tail -f /tmp/agentnex_frontend.log
```

---

## 六、项目结构

```
AgentNex/
├── agent/              # 后端服务
│   ├── main.py         # FastAPI 入口
│   ├── routers/        # API 路由
│   ├── models_db.py    # 数据模型
│   ├── requirements.txt
│   └── venv/           # Python 虚拟环境
├── apps/
│   └── web/            # 前端应用
│       └── src/
├── packages/
│   └── ui/             # 共享 UI 组件
├── .env                # 环境变量
├── docker-compose.yml  # Docker 配置
└── start-venv.sh       # 本地启动脚本
```

---

## 七、开发命令

```bash
# 前端
pnpm dev          # 启动开发服务器
pnpm build        # 构建生产版本
pnpm lint         # 代码检查

# 后端 (在 agent/ 目录，激活虚拟环境后)
python -m agent.main           # 启动服务
pytest                         # 运行测试
```

---

## 技术栈

| 层级 | 技术 |
|-----|------|
| 前端 | React 19, TypeScript, Vite, Tailwind CSS |
| UI 库 | shadcn/ui (基于 Radix UI) |
| 后端 | Python, FastAPI, SQLAlchemy |
| AI | agno, DashScope (通义千问) |
| 数据库 | PostgreSQL |
| 构建工具 | Turbo, pnpm |

---

**问题反馈**: GitHub Issues
