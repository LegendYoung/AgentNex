# AgentNex Platform - 快速上手指南

## 一、第一步：一键启动

```bash
# 1. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 2. 一键启动
docker-compose up -d

# 3. 验证部署
curl http://localhost:8000/
```

**预期结果**：
```json
{
  "status": "ok",
  "message": "AgentNex Platform API is running",
  "version": "2.1.0"
}
```

---

## 二、第二步：登录系统

### 方式 1：使用 Swagger UI

1. 访问 http://localhost:8000/docs
2. 点击 `POST /api/v1/auth/login`
3. 点击 "Try it out"
4. 输入：
   ```json
   {
     "email": "admin@agentnex.io",
     "password": "AgentNex@2026"
   }
   ```
5. 点击 "Execute"
6. 复制返回的 `access_token`

### 方式 2：使用 curl

```bash
# 登录获取 Token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@agentnex.io",
    "password": "AgentNex@2026"
  }'

# 预期返回
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "user": {
    "user_id": "...",
    "email": "admin@agentnex.io",
    "name": "Super Admin",
    "role": "super_admin",
    "require_password_change": true
  }
}
```

---

## 三、第三步：修改密码（首次登录必做）

```bash
# 使用上一步获取的 access_token
ACCESS_TOKEN="eyJ..."

curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "AgentNex@2026",
    "new_password": "YourNewStrong@Pass123"
  }'

# 预期返回
{
  "success": true,
  "message": "Password changed successfully"
}
```

---

## 四、第四步：创建团队

```bash
# 创建团队
curl -X POST http://localhost:8000/api/v1/teams \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "我的第一个团队",
    "description": "这是测试团队"
  }'

# 预期返回
{
  "success": true,
  "data": {
    "team_id": "...",
    "name": "我的第一个团队",
    "description": "这是测试团队"
  }
}
```

---

## 五、第五步：邀请成员

```bash
# 邀请成员（需要团队ID）
TEAM_ID="..."

curl -X POST http://localhost:8000/api/v1/teams/$TEAM_ID/invitations \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "role": "editor"
  }'

# 预期返回
{
  "success": true,
  "data": {
    "invite_code": "...",
    "invite_url": "https://your-domain.com/register?invite=...&email=newuser@example.com",
    "expires_at": "2024-01-02T12:00:00"
  }
}
```

---

## 六、第六步：新用户注册并加入团队

### 方式 1：通过邀请链接

```
访问: https://your-domain.com/register?invite={invite_code}&email=newuser@example.com
```

### 方式 2：手动加入

```bash
# 1. 注册新用户
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "NewUserPass@123",
    "name": "New User"
  }'

# 2. 登录新用户
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "NewUserPass@123"
  }'

# 3. 使用邀请码加入团队
NEW_USER_TOKEN="eyJ..."

curl -X POST http://localhost:8000/api/v1/teams/join \
  -H "Authorization: Bearer $NEW_USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "invite_code": "..."
  }'

# 预期返回
{
  "success": true,
  "data": {
    "team_id": "...",
    "team_name": "我的第一个团队",
    "role": "editor"
  }
}
```

---

## 七、验证清单

### ✅ 部署验证
- [ ] Docker 容器全部运行（`docker-compose ps`）
- [ ] API 健康检查正常（`curl http://localhost:8000/`）
- [ ] Swagger UI 可访问（http://localhost:8000/docs）

### ✅ 用户认证验证
- [ ] 超级管理员登录成功
- [ ] Token 鉴权生效
- [ ] 密码修改成功

### ✅ 团队管理验证
- [ ] 团队创建成功
- [ ] 成员邀请成功
- [ ] 新用户注册成功
- [ ] 通过邀请码加入团队成功

### ✅ 权限控制验证
- [ ] 无 Token 访问受保护接口返回 401
- [ ] 普通用户无法访问管理员接口
- [ ] 团队角色权限生效

---

## 八、常见问题

### Q: Token 过期怎么办？

**A**: 使用 Refresh Token 刷新：

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Authorization: Bearer {refresh_token}"
```

### Q: 忘记密码怎么办？

**A**: 使用超级管理员账号重置：

```bash
# 进入后端容器
docker-compose exec backend bash

# 重置密码
python -c "
from database_postgres import SessionLocal
from models_db import User
from utils.auth import hash_password

db = SessionLocal()
user = db.query(User).filter(User.email == 'user@example.com').first()
user.password_hash = hash_password('NewPass@123')
user.require_password_change = True
db.commit()
"
```

### Q: 如何查看日志？

**A**:
```bash
# 查看所有日志
docker-compose logs -f

# 查看后端日志
docker-compose logs -f backend

# 查看数据库日志
docker-compose logs -f postgres
```

---

## 九、下一步

1. **创建 Agent**：使用 Agent 创建向导（下一阶段开发）
2. **配置知识库**：上传文档，配置 RAG 检索
3. **测试对话**：与 Agent 进行对话测试

---

**技术支持**：
- API 文档：http://localhost:8000/docs
- 部署指南：`DEPLOYMENT.md`
- 问题反馈：GitHub Issues
