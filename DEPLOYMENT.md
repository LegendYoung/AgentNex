# AgentNex Platform - 部署指南

## 一、环境准备

### 必需软件
- Docker Engine 20.10+
- Docker Compose 2.0+
- Git

### 端口要求
- 3000: 前端服务
- 8000: 后端 API 服务
- 5432: PostgreSQL 数据库（可选，仅开发调试）

---

## 二、快速启动（单命令部署）

### 1. 克隆项目
```bash
git clone https://github.com/your-org/agentnex.git
cd agentnex
```

### 2. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑环境变量（必填项）
vi .env
```

**必填项**：
```env
# AI 服务 API Key
DASHSCOPE_API_KEY=your-dashscope-api-key-here

# JWT 密钥（生产环境务必修改）
JWT_SECRET_KEY=$(openssl rand -hex 32)

# 超级管理员（可选，有默认值）
SUPER_ADMIN_EMAIL=admin@agentnex.io
SUPER_ADMIN_PASSWORD=AgentNex@2026
```

### 3. 一键启动
```bash
docker-compose up -d
```

### 4. 验证部署
```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend

# 健康检查
curl http://localhost:8000/
```

### 5. 访问应用
- 前端界面：http://localhost:3000
- API 文档：http://localhost:8000/docs
- 默认账号：`admin@agentnex.io` / `AgentNex@2026`

---

## 三、详细配置说明

### 数据库配置

**PostgreSQL 连接参数**：
```env
POSTGRES_USER=agentnex
POSTGRES_PASSWORD=agentnex123
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=agentnex
```

**数据持久化**：
- 数据库数据：`postgres_data` Docker Volume
- 文件存储：`./agent/data` 目录

### JWT 配置

**生成强随机密钥**：
```bash
openssl rand -hex 32
```

**配置**：
```env
JWT_SECRET_KEY=your-generated-secret-key
```

### AI 服务配置

**DashScope（通义千问）**：
1. 访问 https://dashscope.console.aliyun.com/
2. 创建 API Key
3. 配置环境变量：
```env
DASHSCOPE_API_KEY=sk-xxxxxxxx
```

---

## 四、开发环境部署

### 1. 后端开发

```bash
# 创建 Python 虚拟环境
cd agent
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt.new

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 启动数据库（Docker）
docker-compose up -d postgres

# 初始化数据库和超级管理员
python init_admin.py

# 启动开发服务器
uvicorn main_v2:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端开发

```bash
# 安装依赖
cd apps/web
pnpm install

# 配置 API 地址
echo "VITE_API_URL=http://localhost:8000" > .env

# 启动开发服务器
pnpm dev
```

---

## 五、生产环境部署

### 1. 安全加固

**修改默认密码**：
```env
SUPER_ADMIN_PASSWORD=YourStrongPassword@2026
JWT_SECRET_KEY=$(openssl rand -hex 32)
POSTGRES_PASSWORD=$(openssl rand -hex 16)
```

**配置 HTTPS**：
- 使用 Nginx 反向代理
- 配置 SSL 证书

**CORS 配置**：
```python
# main_v2.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # 限制域名
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)
```

### 2. 性能优化

**数据库连接池**：
```python
# database_postgres.py
engine = create_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)
```

**Redis 缓存（可选）**：
```yaml
# docker-compose.yml
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
```

### 3. 监控与日志

**日志配置**：
```python
# config.py
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)
```

**健康检查**：
```bash
# 定时检查
*/5 * * * * curl -f http://localhost:8000/ || docker-compose restart backend
```

---

## 六、常见问题

### Q1: 数据库连接失败
```bash
# 检查 PostgreSQL 是否启动
docker-compose ps postgres

# 查看日志
docker-compose logs postgres

# 重启数据库
docker-compose restart postgres
```

### Q2: JWT Token 过期
- Access Token 有效期：2 小时
- Refresh Token 有效期：7 天
- 使用 `/api/v1/auth/refresh` 刷新 Token

### Q3: 超级管理员密码忘记
```bash
# 进入后端容器
docker-compose exec backend bash

# 重置密码
python -c "
from database_postgres import SessionLocal
from models_db import User, PlatformRole
from utils.auth import hash_password

db = SessionLocal()
user = db.query(User).filter(User.role == PlatformRole.SUPER_ADMIN).first()
user.password_hash = hash_password('NewPassword@123')
user.require_password_change = True
db.commit()
print('Password reset successfully')
"
```

---

## 七、验收标准

### 部署验收清单

- [ ] Docker 容器全部正常运行（`docker-compose ps`）
- [ ] 健康检查返回正常（`curl http://localhost:8000/`）
- [ ] 超级管理员账号可登录
- [ ] 前端界面可访问（http://localhost:3000）
- [ ] API 文档可访问（http://localhost:8000/docs）
- [ ] 数据库连接正常（可创建/查询数据）

### 功能验收清单

- [ ] 用户注册成功
- [ ] 用户登录成功，获取 Token
- [ ] Token 鉴权生效（无 Token 访问受保护接口返回 401）
- [ ] 团队创建成功
- [ ] 成员邀请成功
- [ ] 通过邀请码加入团队成功
- [ ] 角色权限控制生效

---

## 八、技术支持

- 项目地址：https://github.com/your-org/agentnex
- 问题反馈：https://github.com/your-org/agentnex/issues
- 文档中心：https://docs.agentnex.io
